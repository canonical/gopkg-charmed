# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration test that mirrors the beginner tutorial deployment flow."""

import juju.application
import juju.model
import requests


async def test_tutorial_deploy_and_verify_flow(
    app: juju.application.Application, model: juju.model.Model
) -> None:
    """
    arrange: given the tutorial deployment flow artifacts and a deployed app fixture
    act: when a newcomer-equivalent verification path is executed
    assert: deployment is active, health-check returns 200/ok, and go-import
        metadata endpoint responds with expected metadata marker.
    """
    assert app.status == "active"
    assert len(app.units) == 1

    status = await model.get_status()
    unit_status = status.applications[app.name].units[f"{app.name}/0"]
    address = unit_status.address

    health = requests.get(f"http://{address}:8080/health-check", timeout=10)
    assert health.status_code == 200
    assert health.text == "ok"

    go_get = requests.get(f"http://{address}:8080/yaml.v2?go-get=1", timeout=10)
    assert go_get.status_code == 200
    assert "go-import" in go_get.text
