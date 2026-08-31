# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests that validate executable how-to guide flows."""

import os
import subprocess
from pathlib import Path

import juju.application
import juju.model
import pytest_asyncio
import requests


@pytest_asyncio.fixture(scope="module", name="setup_how_to_contract")
async def setup_how_to_contract_fixture(model: juju.model.Model) -> dict[str, str]:
    """Shared setup contract mirrored from setup how-to prerequisites."""
    charm_dir = Path(__file__).resolve().parents[2]
    app_dir = charm_dir.parent
    repo_root = app_dir.parent
    script = charm_dir / "tests/integration/run_full_local_suite.sh"

    checkout = subprocess.run(
        ["git", "-C", repo_root, "rev-parse", "--show-toplevel"],
        capture_output=True,
        check=True,
        text=True,
    )
    assert Path(checkout.stdout.strip()).resolve() == repo_root
    assert (app_dir / "rockcraft.yaml").is_file()
    assert (charm_dir / "charmcraft.yaml").is_file()
    assert script.exists(), "Missing integration helper script"
    assert os.access(script, os.X_OK), "Integration helper script must be executable"

    status = await model.get_status()
    assert status is not None

    return {"ingress_host": "gopkg.example.com"}


async def _ensure_ingress_configured(model: juju.model.Model, ingress_host: str) -> None:
    ingress_name = "nginx-ingress-integrator"
    app_name = "gopkg-charmed"

    if ingress_name not in model.applications:
        await model.deploy(
            "nginx-ingress-integrator",
            application_name=ingress_name,
            channel="latest/stable",
            trust=True,
        )

    relation_exists = any(relation.matches(ingress_name, app_name) for relation in model.relations)
    if not relation_exists:
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


async def test_how_to_guides_flow(
    app: juju.application.Application,
    model: juju.model.Model,
    setup_how_to_contract: dict[str, str],
) -> None:
    """
    arrange: given setup-guide prerequisites and a deployed gopkg app
    act: when ingress and hostname are configured per the how-to guides
    assert: routing, metadata, settings, and the local helper contract work.
    """
    assert app.status == "active"
    await _ensure_ingress_configured(model, setup_how_to_contract["ingress_host"])

    health = requests.get(
        "http://127.0.0.1/health-check",
        headers={"Host": setup_how_to_contract["ingress_host"]},
        timeout=20,
    )
    assert health.status_code == 200
    assert health.text == "ok"

    app = model.applications["gopkg-charmed"]
    await app.set_config({"hostname": "staging.example.com"})
    await model.wait_for_idle(apps=["gopkg-charmed"], status="active", timeout=15 * 60)

    go_get = requests.get(
        "http://127.0.0.1/yaml.v2?go-get=1",
        headers={"Host": setup_how_to_contract["ingress_host"]},
        timeout=20,
    )
    assert go_get.status_code == 200
    assert "go-import" in go_get.text
    assert "staging.example.com" in go_get.text

    ingress = model.applications["nginx-ingress-integrator"]
    config = await ingress.get_config()
    assert config["service-hostname"]["value"] == setup_how_to_contract["ingress_host"]
    assert config["path-routes"]["value"] == "/"
    assert config["rewrite-enabled"]["value"] is False

    script = Path(__file__).resolve().parent / "run_full_local_suite.sh"
    content = script.read_text(encoding="utf-8")
    assert 'tox --workdir "$TOX_WORK_DIR" -e integration' in content
    assert "id -nG | grep -qw snap_microk8s" in content
    assert "microk8s status --wait-ready" in content
    assert "microk8s kubectl rollout status deployment/registry" in content
    assert "curl --fail --silent --show-error http://127.0.0.1:32000/v2/" in content
    assert "rockcraft pack" in content
    assert '[[ ! -d "$REPO_ROOT/.git"' in content
