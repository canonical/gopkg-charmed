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


async def test_tutorial_ingress_and_hostname_flow(model: juju.model.Model) -> None:
    """
    arrange: given a deployed gopkg app and an ingress integrator
    act: when ingress host routing and charm hostname config are applied as in
        the tutorial
    assert: host-routed health/go-import requests succeed and go-import metadata
        reflects the updated charm hostname.
    """
    app_name = "gopkg-charmed"
    ingress_name = "nginx-ingress-integrator"
    ingress_host = "gopkg.example.com"

    if ingress_name not in model.applications:
        await model.deploy(
            "nginx-ingress-integrator",
            application_name=ingress_name,
            channel="latest/stable",
            trust=True,
        )

    await model.integrate(ingress_name, app_name)

    ingress = model.applications[ingress_name]
    await ingress.set_config(
        {
            "service-hostname": ingress_host,
            "path-routes": "/",
            "rewrite-enabled": "false",
        }
    )

    await model.wait_for_idle(apps=[app_name, ingress_name], status="active", timeout=15 * 60)

    health = requests.get(
        "http://127.0.0.1/health-check",
        headers={"Host": ingress_host},
        timeout=20,
    )
    assert health.status_code == 200
    assert health.text == "ok"

    go_get = requests.get(
        "http://127.0.0.1/yaml.v2?go-get=1",
        headers={"Host": ingress_host},
        timeout=20,
    )
    assert go_get.status_code == 200
    assert "go-import" in go_get.text

    app = model.applications[app_name]
    await app.set_config({"hostname": "staging.example.com"})
    await model.wait_for_idle(apps=[app_name], status="active", timeout=15 * 60)

    go_get_updated = requests.get(
        "http://127.0.0.1/yaml.v2?go-get=1",
        headers={"Host": ingress_host},
        timeout=20,
    )
    assert go_get_updated.status_code == 200
    assert "staging.example.com" in go_get_updated.text
