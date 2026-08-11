# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for the gopkg charm."""

import juju.application
import juju.model
import requests


async def test_active_after_deploy(app: juju.application.Application) -> None:
    """
    arrange: given the packed gopkg charm and rock image
    act: when the charm is deployed with the app-image resource
    assert: the application reaches active status (asserted by the app
        fixture's wait_for_idle) and reports exactly one unit.
    """
    assert app.status == "active"

    assert len(app.units) == 1


async def test_health_check_endpoint(
    app: juju.application.Application, model: juju.model.Model
) -> None:
    """
    arrange: given an active gopkg deployment
    act: when the /health-check endpoint is requested on the unit address
        at the default APP_PORT
    assert: the application answers 200 with the body "ok".
    """
    status = await model.get_status()
    unit_status = status.applications[app.name].units[f"{app.name}/0"]
    address = unit_status.address

    response = requests.get(f"http://{address}:8080/health-check", timeout=10)

    assert response.status_code == 200
    assert response.text == "ok"
