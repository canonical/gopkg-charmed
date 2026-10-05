# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm integration tests.

Requires a bootstrapped Juju controller and ``build/artifacts.build.yaml``:
``opcli artifacts build`` writes it, ``opcli artifacts push-images`` adds the
image reference, and in CI charm-ci does both. charm-ci's pytest plugin reads
the file and provides the ``charm_path`` and ``resource_images`` fixtures.

Tests use Jubilant: ``gopkg_app`` deploys the charm into pytest-jubilant's
``juju`` model.
"""

import platform

import jubilant
import pytest

APP_NAME = "gopkg-k8s"
_ARCH_MAP = {"aarch64": "arm64", "x86_64": "amd64"}


@pytest.fixture(scope="module", name="gopkg_app")
def gopkg_app_fixture(
    juju: jubilant.Juju, charm_path: str, resource_images: dict[str, str]
) -> str:
    """Deploy gopkg-k8s into the module's model and return its application name."""
    # Fresh per-run models default to amd64 pods; match the actual host so
    # the pod can schedule on arm64 dev VMs and amd64 CI runners alike.
    juju.model_constraints({"arch": _ARCH_MAP.get(platform.machine(), "amd64")})
    juju.deploy(charm_path, app=APP_NAME, resources=resource_images)
    try:
        juju.wait(lambda status: jubilant.all_active(status, APP_NAME), timeout=15 * 60)
    except Exception:
        # Surface the real cause in CI logs: spread destroys the model after
        # the run, so this is the only chance to see the hook traceback.
        print("==== juju debug-log (tail) ====")
        print(juju.debug_log(limit=200))
        raise
    return APP_NAME
