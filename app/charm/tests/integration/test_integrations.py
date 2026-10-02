# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for the gopkg charm's relation endpoints.

The go-framework extension gives the charm four endpoints: ``ingress`` and
``logging`` (requires), ``metrics-endpoint`` and ``grafana-dashboard``
(provides). Each test integrates one of them with a published charm that
offers the counterpart and checks that both sides settle in ``active``, which
is what the Charmhub listing review requires for every endpoint.

The COS charms on ``2/stable`` are published for amd64 only, so their tests
are skipped on arm64 hosts such as an Apple Silicon Multipass VM; the ingress
test runs on both architectures.
"""

import logging
import os
import platform
import re
import subprocess
import time
import typing

import jubilant
import pytest
import requests

logger = logging.getLogger(__name__)

INGRESS_HOST = "gopkg.example.com"
INGRESS_CHARM = "nginx-ingress-integrator"
INGRESS_CHANNEL = "latest/stable"
# Empty uses the cluster's default ingress class, which MicroK8s's nginx is.
# CI sets "cilium" for Canonical Kubernetes (see spread.yaml).
INGRESS_CLASS = os.environ.get("INGRESS_CLASS", "")
COS_CHANNEL = "2/stable"
LOKI = "loki-k8s"
PROMETHEUS = "prometheus-k8s"
GRAFANA = "grafana-k8s"

requires_amd64 = pytest.mark.skipif(
    platform.machine() not in ("x86_64", "amd64"),
    reason=f"the COS charms on {COS_CHANNEL} are published for amd64 only",
)


@pytest.fixture(scope="module", name="ingress")
def ingress_fixture(juju: jubilant.Juju, gopkg_app: str) -> str:
    """nginx-ingress-integrator, configured as in the tutorial apart from path-routes."""
    juju.deploy(
        INGRESS_CHARM,
        channel=INGRESS_CHANNEL,
        trust=True,
        # rewrite-enabled=false is essential: the default rewrites every path
        # to "/", so the service would answer its root redirect for every URL.
        config={
            "service-hostname": INGRESS_HOST,
            # paas-charm requests strip-prefix, which makes the integrator write
            # its paths as regular expressions (use-regex=false cannot override
            # that). Cilium matches a regex against the whole URL path, so "/"
            # would route only the root; "/.*" routes every path on both Cilium
            # and nginx.
            "path-routes": "/.*",
            "rewrite-enabled": "false",
            "ingress-class": INGRESS_CLASS,
        },
    )
    # The service never reads the Host header: it renders its own `hostname`
    # option into go-import metadata. Routing and metadata are separate
    # settings, so the tutorial sets both to the same name.
    juju.config(gopkg_app, {"hostname": INGRESS_HOST})
    juju.integrate(f"{gopkg_app}:ingress", f"{INGRESS_CHARM}:ingress")
    juju.wait(
        lambda status: jubilant.all_active(status, gopkg_app, INGRESS_CHARM), timeout=15 * 60
    )
    return INGRESS_CHARM


def _stuck_in_patch_race(
    juju: jubilant.Juju, names: tuple[str, ...], timeout: int, grace: int = 120
) -> list[str]:
    """Wait until every application in ``names`` is active.

    Returns the applications whose units have been blocked with a Kubernetes
    "Unauthorized" error for longer than ``grace`` seconds, or an empty list
    once everything is active. Raises when ``timeout`` expires first.
    """
    deadline = time.monotonic() + timeout
    first_seen: dict[str, float] = {}
    while time.monotonic() < deadline:
        status = juju.status()
        all_active = True
        stuck: list[str] = []
        for name in names:
            application = status.apps.get(name)
            units = list(application.units.values()) if application else []
            if not units or any(unit.workload_status.current != "active" for unit in units):
                all_active = False
            if any(
                unit.workload_status.current == "blocked"
                and "Unauthorized" in unit.workload_status.message
                for unit in units
            ):
                first_seen.setdefault(name, time.monotonic())
                if time.monotonic() - first_seen[name] > grace:
                    stuck.append(name)
            else:
                first_seen.pop(name, None)
        if all_active:
            return []
        if stuck:
            return stuck
        time.sleep(15)
    raise AssertionError(f"timed out after {timeout}s waiting for {names} to become active")


@pytest.fixture(scope="module", name="cos")
def cos_fixture(juju: jubilant.Juju) -> None:
    """Loki, Prometheus and Grafana from COS, deployed side by side.

    A COS charm occasionally ends up blocked with "... patch failed:
    Unauthorized" after patching its own StatefulSet resource limits: the
    Kubernetes API rejects the unit's service-account token and the charm
    does not retry on its own, so the unit stays blocked indefinitely. This
    is a Juju/COS race unrelated to gopkg; the fixture redeploys such an
    application once instead of failing every test in the module.
    """
    names = (LOKI, PROMETHEUS, GRAFANA)
    for name in names:
        juju.deploy(name, channel=COS_CHANNEL, trust=True)
    for attempt in (1, 2):
        stuck = _stuck_in_patch_race(juju, names, timeout=20 * 60)
        if not stuck:
            break
        if attempt == 2:
            raise AssertionError(
                f"{stuck} stayed blocked by the Kubernetes patch race after a redeploy"
            )
        logger.warning("%s blocked by the Kubernetes patch race; redeploying once", stuck)
        for name in stuck:
            juju.remove_application(name, destroy_storage=True, force=True)
            juju.wait(lambda status, name=name: name not in status.apps, timeout=10 * 60)
            juju.deploy(name, channel=COS_CHANNEL, trust=True)
    juju.wait(lambda status: jubilant.all_active(status, *names), timeout=5 * 60)


def _unit_address(juju: jubilant.Juju, app: str) -> str:
    return juju.status().apps[app].units[f"{app}/0"].address


def _ingress_address(juju: jubilant.Juju, ingress: str) -> str:
    """Return the ingress controller's address that the integrator reports.

    The integrator's unit status reads "Ingress IP(s): <address>, ...".
    MicroK8s's nginx listens on the host, so 127.0.0.1 is the fallback.
    """
    message = juju.status().apps[ingress].units[f"{ingress}/0"].workload_status.message
    match = re.search(r"Ingress IP\(s\): ([^,\s]+)", message)
    return match.group(1) if match else "127.0.0.1"


def _kubectl_report(namespace: str) -> str:
    """Return what kubectl shows about the ingress path, for failure messages."""
    report = []
    for args in (
        ["get", "ingress,service,endpoints", "-n", namespace, "-o", "wide"],
        ["get", "service,endpoints", "cilium-ingress", "-n", "kube-system", "-o", "wide"],
    ):
        try:
            result = subprocess.run(
                ["kubectl", *args], capture_output=True, text=True, timeout=30, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            report.append(f"$ kubectl {' '.join(args)}\n{exc}")
        else:
            report.append(f"$ kubectl {' '.join(args)}\n{result.stdout}{result.stderr}")
    return "\n".join(report)


def _get_through_ingress(
    juju: jubilant.Juju, address: str, path: str, params: dict[str, str] | None = None
) -> requests.Response:
    """Request ``path`` through the ingress controller until it answers 200.

    On timeout, the error shows the last answer and the cluster's ingress
    objects, because spread discards the cluster after the run.
    """
    deadline = time.monotonic() + 5 * 60
    last = "no request completed"
    while time.monotonic() < deadline:
        try:
            response = requests.get(
                f"http://{address}{path}",
                params=params,
                headers={"Host": INGRESS_HOST},
                timeout=10,
            )
        except requests.RequestException as exc:
            answer = repr(exc)
        else:
            if response.status_code == 200:
                return response
            answer = f"HTTP {response.status_code}: {response.text[:200]!r}"
        if answer != last:
            logger.info("%s through %s: %s", path, address, answer)
            last = answer
        time.sleep(10)
    raise AssertionError(
        f"{path} did not answer 200 through {address} within 5 minutes; last: {last}\n"
        f"{_kubectl_report(juju.model or '')}"
    )


def _related(juju: jubilant.Juju, app_a: str, app_b: str) -> bool:
    relations = juju.status().apps[app_a].relations
    return any(
        relation.related_app == app_b for related in relations.values() for relation in related
    )


def _wait_until(
    probe: typing.Callable[[], typing.Any], what: str, timeout: int = 5 * 60, interval: int = 10
) -> typing.Any:
    """Poll ``probe`` until it returns a truthy value; HTTP errors are retried."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            result = probe()
        except requests.RequestException as exc:
            last_error = exc
        else:
            if result:
                return result
        time.sleep(interval)
    raise AssertionError(
        f"timed out after {timeout}s waiting for {what}; last error: {last_error}"
    )


def test_ingress_routes_to_the_service(juju: jubilant.Juju, ingress: str) -> None:
    """
    arrange: given the charm integrated with nginx-ingress-integrator routing
        gopkg.example.com to it
    act: when the health endpoint is requested through the ingress controller
        with that Host header
    assert: the response is 200 with the body "ok", so the ingress relation
        carries the service's address and port to the integrator.
    """
    assert juju.status().apps[ingress].app_status.current == "active"
    address = _ingress_address(juju, ingress)

    response = _get_through_ingress(juju, address, "/health-check")

    assert response.text == "ok"


def test_ingress_serves_go_import_for_the_routed_host(juju: jubilant.Juju, ingress: str) -> None:
    """
    arrange: given the charm integrated with nginx-ingress-integrator routing
        gopkg.example.com to it, and its hostname option set to the same name
    act: when a package path is requested through the ingress with ?go-get=1,
        which is the query the Go tool sends to resolve an import path
    assert: the go-import meta tag names the routed host as the import
        prefix. The Go tool rejects a tag whose prefix differs from the import
        path it asked for, so a health check alone cannot prove that
        `go get gopkg.example.com/yaml.v2` would work.
    """
    assert juju.status().apps[ingress].app_status.current == "active"
    address = _ingress_address(juju, ingress)

    response = _get_through_ingress(juju, address, "/yaml.v2", params={"go-get": "1"})

    tag = re.search(r'<meta name="go-import" content="([^"]*)"', response.text)
    assert tag, f"no go-import meta tag in:\n{response.text}"
    prefix, vcs, repo_root = tag.group(1).split()
    assert prefix == f"{INGRESS_HOST}/yaml.v2"
    assert vcs == "git"
    assert repo_root == f"https://{INGRESS_HOST}/yaml.v2"


@requires_amd64
def test_logging_integration_settles(juju: jubilant.Juju, gopkg_app: str, cos: None) -> None:
    """
    arrange: given the charm and loki-k8s deployed in the same model
    act: when the charm's logging endpoint is integrated with Loki's
    assert: both applications return to active, and a request to the service
        shows up in Loki as a log stream labelled with the application name.
    """
    juju.integrate(f"{gopkg_app}:logging", f"{LOKI}:logging")
    juju.wait(lambda status: jubilant.all_active(status, gopkg_app, LOKI), timeout=15 * 60)
    assert _related(juju, gopkg_app, LOKI)
    # Any non-health request writes one structured log record to stdout,
    # which Pebble forwards to Loki with the unit's Juju topology labels.
    app_address = _unit_address(juju, gopkg_app)
    loki_address = _unit_address(juju, LOKI)
    requests.get(f"http://{app_address}:8080/", timeout=10, allow_redirects=False)

    def log_stream_labelled_with_app() -> list[str] | None:
        response = requests.get(
            f"http://{loki_address}:3100/loki/api/v1/label/juju_application/values", timeout=10
        )
        response.raise_for_status()
        values = response.json().get("data") or []
        return values if gopkg_app in values else None

    labels = _wait_until(log_stream_labelled_with_app, f"Loki to receive logs from {gopkg_app}")

    assert gopkg_app in labels


@requires_amd64
def test_metrics_endpoint_is_scraped(juju: jubilant.Juju, gopkg_app: str, cos: None) -> None:
    """
    arrange: given the charm and prometheus-k8s deployed in the same model
    act: when the charm's metrics-endpoint is integrated with Prometheus
    assert: both applications return to active and Prometheus reports a
        healthy scrape target labelled with the charm's application name,
        so the workload's metrics endpoint is really being scraped.
    """
    juju.integrate(f"{gopkg_app}:metrics-endpoint", f"{PROMETHEUS}:metrics-endpoint")
    juju.wait(lambda status: jubilant.all_active(status, gopkg_app, PROMETHEUS), timeout=15 * 60)
    address = _unit_address(juju, PROMETHEUS)

    def healthy_scrape_target() -> list[dict[str, typing.Any]] | None:
        response = requests.get(f"http://{address}:9090/api/v1/targets", timeout=10)
        response.raise_for_status()
        targets = response.json()["data"]["activeTargets"]
        matching = [t for t in targets if t["labels"].get("juju_application") == gopkg_app]
        return matching if matching and all(t["health"] == "up" for t in matching) else None

    targets = _wait_until(
        healthy_scrape_target, f"a healthy Prometheus scrape target for {gopkg_app}"
    )

    assert targets


@requires_amd64
def test_grafana_dashboard_integration_settles(
    juju: jubilant.Juju, gopkg_app: str, cos: None
) -> None:
    """
    arrange: given the charm and grafana-k8s deployed in the same model
    act: when the charm's grafana-dashboard endpoint is integrated with Grafana
    assert: both applications return to active and the relation is
        established.
    """
    juju.integrate(f"{gopkg_app}:grafana-dashboard", f"{GRAFANA}:grafana-dashboard")
    juju.wait(lambda status: jubilant.all_active(status, gopkg_app, GRAFANA), timeout=15 * 60)

    assert _related(juju, gopkg_app, GRAFANA)
