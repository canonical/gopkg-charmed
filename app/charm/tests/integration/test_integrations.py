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
import platform
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
    """nginx-ingress-integrator, configured as in the tutorial and integrated."""
    ingress = await model.deploy(
        INGRESS_CHARM,
        channel=INGRESS_CHANNEL,
        trust=True,
        # rewrite-enabled=false is essential: the default rewrites every path
        # to "/", so the service would answer its root redirect for every URL.
        config={
            "service-hostname": INGRESS_HOST,
            "path-routes": "/",
            "rewrite-enabled": "false",
        },
    )
    await model.integrate(f"{app.name}:ingress", f"{ingress.name}:ingress")
    await model.wait_for_idle(apps=[app.name, ingress.name], status="active", timeout=15 * 60)
    return ingress


@pytest_asyncio.fixture(scope="module", name="cos")
async def cos_fixture(model: juju.model.Model) -> dict[str, juju.application.Application]:
    """Loki, Prometheus and Grafana from COS, deployed side by side."""
    apps = {}
    for name in (LOKI, PROMETHEUS, GRAFANA):
        apps[name] = await model.deploy(name, channel=COS_CHANNEL, trust=True)
    await model.wait_for_idle(apps=list(apps), status="active", timeout=20 * 60)
    return apps


async def _unit_address(model: juju.model.Model, app: juju.application.Application) -> str:
    status = await model.get_status()
    return status.applications[app.name].units[f"{app.name}/0"].address


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
    app: juju.application.Application, ingress: juju.application.Application
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

    def health_through_ingress() -> requests.Response | None:
        response = requests.get(
            "http://127.0.0.1/health-check", headers={"Host": INGRESS_HOST}, timeout=10
        )
        return response if response.status_code == 200 else None

    response = await _wait_until(health_through_ingress, "the ingress to route /health-check")

    assert response.text == "ok"


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
