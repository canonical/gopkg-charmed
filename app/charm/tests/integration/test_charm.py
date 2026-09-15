# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for the gopkg charm."""

import juju.application
import juju.model
import requests


async def test_deploy_and_health_check(
    app: juju.application.Application, model: juju.model.Model
) -> None:
    """
    arrange: given the packed gopkg charm and rock image
    act: when the charm is deployed and its health endpoint is requested
    assert: one unit is active and answers 200 with the body "ok".
    """
    assert app.status == "active"
    assert len(app.units) == 1

    status = await model.get_status()
    unit_status = status.applications[app.name].units[f"{app.name}/0"]
    address = unit_status.address

    response = requests.get(f"http://{address}:8080/health-check", timeout=10)

    assert response.status_code == 200
    assert response.text == "ok"


async def test_metrics_endpoint_serves_application_metrics(
    app: juju.application.Application, model: juju.model.Model
) -> None:
    """
    arrange: given the deployed charm, whose metrics-port option defaults to
        the application port
    act: when the health endpoint and then the framework's default metrics path
        are requested on that port
    assert: the metrics endpoint answers 200 with Go runtime metrics and the
        request counter that the health check just incremented.
    """
    status = await model.get_status()
    address = status.applications[app.name].units[f"{app.name}/0"].address
    requests.get(f"http://{address}:8080/health-check", timeout=10)

    response = requests.get(f"http://{address}:8080/metrics", timeout=10)

    assert response.status_code == 200
    assert "go_goroutines" in response.text
    assert 'gopkg_http_requests_total{method="GET",route="health_check"' in response.text
