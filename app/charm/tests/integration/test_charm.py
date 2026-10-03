# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for the gopkg charm."""

import jubilant
import requests


def test_deploy_and_health_check(juju: jubilant.Juju, gopkg_app: str) -> None:
    """
    arrange: given the packed gopkg charm and rock image
    act: when the charm is deployed and its health endpoint is requested
    assert: one unit is active and answers 200 with the body "ok".
    """
    app = juju.status().apps[gopkg_app]
    assert app.app_status.current == "active"
    assert len(app.units) == 1

    address = app.units[f"{gopkg_app}/0"].address

    response = requests.get(f"http://{address}:8080/health-check", timeout=10)

    assert response.status_code == 200
    assert response.text == "ok"


def test_metrics_endpoint_serves_application_metrics(juju: jubilant.Juju, gopkg_app: str) -> None:
    """
    arrange: given the deployed charm, whose metrics-port option defaults to
        the application port
    act: when the health endpoint and then the framework's default metrics path
        are requested on that port
    assert: the metrics endpoint answers 200 with Go runtime metrics and the
        request counter that the health check just incremented.
    """
    address = juju.status().apps[gopkg_app].units[f"{gopkg_app}/0"].address
    requests.get(f"http://{address}:8080/health-check", timeout=10)

    response = requests.get(f"http://{address}:8080/metrics", timeout=10)

    assert response.status_code == 200
    assert "go_goroutines" in response.text
    assert 'gopkg_http_requests_total{method="GET",route="health_check"' in response.text
