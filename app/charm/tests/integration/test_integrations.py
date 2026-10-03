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

import asyncio
import logging
import os
import platform
import re
import subprocess
import time
import typing

import juju.application
import juju.model
import pytest
import pytest_asyncio
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


@pytest_asyncio.fixture(scope="module", name="ingress")
async def ingress_fixture(
    model: juju.model.Model, app: juju.application.Application
) -> juju.application.Application:
    """nginx-ingress-integrator, configured as in the tutorial apart from path-routes."""
    ingress = await model.deploy(
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
    await app.set_config({"hostname": INGRESS_HOST})
    await model.integrate(f"{app.name}:ingress", f"{ingress.name}:ingress")
    await model.wait_for_idle(apps=[app.name, ingress.name], status="active", timeout=15 * 60)
    return ingress


async def _stuck_in_patch_race(
    model: juju.model.Model, names: tuple[str, ...], timeout: int, grace: int = 120
) -> list[str]:
    """Wait until every application in ``names`` is active.

    Returns the applications whose units have been blocked with a Kubernetes
    "Unauthorized" error for longer than ``grace`` seconds, or an empty list
    once everything is active. Raises when ``timeout`` expires first.
    """
    deadline = time.monotonic() + timeout
    first_seen: dict[str, float] = {}
    while time.monotonic() < deadline:
        status = await model.get_status()
        all_active = True
        stuck: list[str] = []
        for name in names:
            application = status.applications.get(name)
            units = list(application.units.values()) if application else []
            if not units or any(unit.workload_status.status != "active" for unit in units):
                all_active = False
            if any(
                unit.workload_status.status == "blocked"
                and "Unauthorized" in (unit.workload_status.info or "")
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
        await asyncio.sleep(15)
    raise AssertionError(f"timed out after {timeout}s waiting for {names} to become active")


@pytest_asyncio.fixture(scope="module", name="cos")
async def cos_fixture(model: juju.model.Model) -> dict[str, juju.application.Application]:
    """Loki, Prometheus and Grafana from COS, deployed side by side.

    A COS charm occasionally ends up blocked with "... patch failed:
    Unauthorized" after patching its own StatefulSet resource limits: the
    Kubernetes API rejects the unit's service-account token and the charm
    does not retry on its own, so the unit stays blocked indefinitely. This
    is a Juju/COS race unrelated to gopkg; the fixture redeploys such an
    application once instead of failing every test in the module.
    """
    names = (LOKI, PROMETHEUS, GRAFANA)
    apps = {}
    for name in names:
        apps[name] = await model.deploy(name, channel=COS_CHANNEL, trust=True)
    for attempt in (1, 2):
        stuck = await _stuck_in_patch_race(model, names, timeout=20 * 60)
        if not stuck:
            break
        if attempt == 2:
            raise AssertionError(
                f"{stuck} stayed blocked by the Kubernetes patch race after a redeploy"
            )
        logger.warning("%s blocked by the Kubernetes patch race; redeploying once", stuck)
        for name in stuck:
            await model.remove_application(
                name, block_until_done=True, destroy_storage=True, force=True
            )
            apps[name] = await model.deploy(name, channel=COS_CHANNEL, trust=True)
    await model.wait_for_idle(apps=list(names), status="active", timeout=5 * 60)
    return apps


async def _unit_address(model: juju.model.Model, app: juju.application.Application) -> str:
    status = await model.get_status()
    return status.applications[app.name].units[f"{app.name}/0"].address


async def _ingress_address(model: juju.model.Model, ingress: juju.application.Application) -> str:
    """Return the ingress controller's address that the integrator reports.

    The integrator's status reads "Ingress IP(s): <address>, ...". MicroK8s's
    nginx listens on the host, so 127.0.0.1 is the fallback.
    """
    status = await model.get_status()
    message = status.applications[ingress.name].status.info or ""
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


async def _get_through_ingress(
    model: juju.model.Model, address: str, path: str, params: dict[str, str] | None = None
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
        await asyncio.sleep(10)
    raise AssertionError(
        f"{path} did not answer 200 through {address} within 5 minutes; last: {last}\n"
        f"{_kubectl_report(model.name)}"
    )


async def _related(model: juju.model.Model, app_a: str, app_b: str) -> bool:
    status = await model.get_status()
    for relation in status.relations:
        applications = {endpoint.application for endpoint in relation.endpoints}
        if {app_a, app_b} <= applications:
            return True
    return False


async def _wait_until(
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
        await asyncio.sleep(interval)
    raise AssertionError(
        f"timed out after {timeout}s waiting for {what}; last error: {last_error}"
    )


async def test_ingress_routes_to_the_service(
    model: juju.model.Model,
    app: juju.application.Application,
    ingress: juju.application.Application,
) -> None:
    """
    arrange: given the charm integrated with nginx-ingress-integrator routing
        gopkg.example.com to it
    act: when the health endpoint is requested through the ingress controller
        with that Host header
    assert: the response is 200 with the body "ok", so the ingress relation
        carries the service's address and port to the integrator.
    """
    assert ingress.status == "active"
    address = await _ingress_address(model, ingress)

    response = await _get_through_ingress(model, address, "/health-check")

    assert response.text == "ok"


async def test_ingress_serves_go_import_for_the_routed_host(
    model: juju.model.Model,
    app: juju.application.Application,
    ingress: juju.application.Application,
) -> None:
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
    assert ingress.status == "active"
    address = await _ingress_address(model, ingress)

    response = await _get_through_ingress(model, address, "/yaml.v2", params={"go-get": "1"})

    tag = re.search(r'<meta name="go-import" content="([^"]*)"', response.text)
    assert tag, f"no go-import meta tag in:\n{response.text}"
    prefix, vcs, repo_root = tag.group(1).split()
    assert prefix == f"{INGRESS_HOST}/yaml.v2"
    assert vcs == "git"
    assert repo_root == f"https://{INGRESS_HOST}/yaml.v2"


@requires_amd64
async def test_logging_integration_settles(
    app: juju.application.Application,
    model: juju.model.Model,
    cos: dict[str, juju.application.Application],
) -> None:
    """
    arrange: given the charm and loki-k8s deployed in the same model
    act: when the charm's logging endpoint is integrated with Loki's
    assert: both applications return to active, and a request to the service
        shows up in Loki as a log stream labelled with the application name.
    """
    loki = cos[LOKI]

    await model.integrate(f"{app.name}:logging", f"{loki.name}:logging")
    await model.wait_for_idle(apps=[app.name, loki.name], status="active", timeout=15 * 60)
    assert await _related(model, app.name, loki.name)
    # Any non-health request writes one structured log record to stdout,
    # which Pebble forwards to Loki with the unit's Juju topology labels.
    app_address = await _unit_address(model, app)
    loki_address = await _unit_address(model, loki)
    requests.get(f"http://{app_address}:8080/", timeout=10, allow_redirects=False)

    def log_stream_labelled_with_app() -> list[str] | None:
        response = requests.get(
            f"http://{loki_address}:3100/loki/api/v1/label/juju_application/values", timeout=10
        )
        response.raise_for_status()
        values = response.json().get("data") or []
        return values if app.name in values else None

    labels = await _wait_until(
        log_stream_labelled_with_app, f"Loki to receive logs from {app.name}"
    )

    assert app.name in labels


@requires_amd64
async def test_metrics_endpoint_is_scraped(
    app: juju.application.Application,
    model: juju.model.Model,
    cos: dict[str, juju.application.Application],
) -> None:
    """
    arrange: given the charm and prometheus-k8s deployed in the same model
    act: when the charm's metrics-endpoint is integrated with Prometheus
    assert: both applications return to active and Prometheus reports a
        healthy scrape target labelled with the charm's application name,
        so the workload's metrics endpoint is really being scraped.
    """
    prometheus = cos[PROMETHEUS]

    await model.integrate(f"{app.name}:metrics-endpoint", f"{prometheus.name}:metrics-endpoint")
    await model.wait_for_idle(apps=[app.name, prometheus.name], status="active", timeout=15 * 60)
    address = await _unit_address(model, prometheus)

    def healthy_scrape_target() -> list[dict[str, typing.Any]] | None:
        response = requests.get(f"http://{address}:9090/api/v1/targets", timeout=10)
        response.raise_for_status()
        targets = response.json()["data"]["activeTargets"]
        matching = [t for t in targets if t["labels"].get("juju_application") == app.name]
        return matching if matching and all(t["health"] == "up" for t in matching) else None

    targets = await _wait_until(
        healthy_scrape_target, f"a healthy Prometheus scrape target for {app.name}"
    )

    assert targets


@requires_amd64
async def test_grafana_dashboard_integration_settles(
    app: juju.application.Application,
    model: juju.model.Model,
    cos: dict[str, juju.application.Application],
) -> None:
    """
    arrange: given the charm and grafana-k8s deployed in the same model
    act: when the charm's grafana-dashboard endpoint is integrated with Grafana
    assert: both applications return to active and the relation is
        established.
    """
    grafana = cos[GRAFANA]

    await model.integrate(f"{app.name}:grafana-dashboard", f"{grafana.name}:grafana-dashboard")
    await model.wait_for_idle(apps=[app.name, grafana.name], status="active", timeout=15 * 60)

    assert await _related(model, app.name, grafana.name)
