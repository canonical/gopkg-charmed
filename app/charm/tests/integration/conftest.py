# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm integration tests.

Requires a bootstrapped Juju controller (e.g. the MicroK8s cloud from the
README deployment guide). Configuration via environment variables:

- CHARM_FILE: path to a packed charm (default: first gopkg_*.charm in CWD)
- APP_IMAGE:  OCI image reference for the app-image resource; overrides
              automatic discovery from ``build/artifacts.build.yaml``
              (default when neither is available: localhost:32000/gopkg:0.1)
"""

import glob
import logging
import os
import platform
import subprocess
from pathlib import Path

import yaml

# python-libjuju types, not ops.model: pytest-operator's ops_test.model is a
# juju.model.Model (which has deploy/wait_for_idle); the similarly named
# charm-side ops.model.Model does not.
import juju.application
import juju.model
import pytest_asyncio
import pytest_operator.plugin

_log = logging.getLogger(__name__)

_DEFAULT_APP_IMAGE = "localhost:32000/gopkg:0.1"
_ARCH_MAP = {"aarch64": "arm64", "x86_64": "amd64"}


def _resolve_app_image() -> str:
    """Return the OCI image reference for the gopkg app-image resource.

    Lookup order:
    1. ``APP_IMAGE`` environment variable (explicit override, e.g. local dev).
    2. ``build/artifacts.build.yaml`` discovered by walking up from this file
       (written by ``opcli artifacts fetch/push-images`` in CI); uses the
       image ref for the current host architecture.
    3. ``localhost:32000/gopkg:0.1`` (default for local dev with a local registry).
    """
    env_image = os.environ.get("APP_IMAGE")
    if env_image:
        return env_image

    arch = _ARCH_MAP.get(platform.machine(), "amd64")
    here = Path(__file__).resolve().parent
    for directory in [here, *here.parents]:
        candidate = directory / "build" / "artifacts.build.yaml"
        if candidate.is_file():
            try:
                with open(candidate) as fh:
                    data = yaml.safe_load(fh)
                for rock in data.get("rocks", []):
                    if rock.get("name") == "gopkg":
                        for build in rock.get("builds", []):
                            if build.get("arch") == arch and build.get("image"):
                                image = build["image"]
                                _log.info("Resolved app-image from %s: %s", candidate, image)
                                return image
            except Exception as exc:
                _log.warning("Failed to read %s: %s", candidate, exc)
            break

    _log.info("Using default app-image: %s", _DEFAULT_APP_IMAGE)
    return _DEFAULT_APP_IMAGE


@pytest_asyncio.fixture(scope="module", name="model")
async def model_fixture(ops_test: pytest_operator.plugin.OpsTest) -> juju.model.Model:
    """The current test model."""
    assert ops_test.model
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="app")
async def app_fixture(model: juju.model.Model) -> juju.application.Application:
    """The deployed gopkg application."""
    charm_file = os.environ.get("CHARM_FILE")
    if not charm_file:
        # charm-ci builds the charm in a separate phase and places it in the
        # project tree, not necessarily the tox working directory - search
        # here first, then recursively from the repository root.
        for pattern in ("gopkg_*.charm", "../../gopkg_*.charm", "../../**/gopkg_*.charm"):
            matches = sorted(glob.glob(pattern, recursive=True))
            if matches:
                charm_file = matches[0]
                break

    if not charm_file:
        raise FileNotFoundError(
            "No charm file found. Set CHARM_FILE environment variable or "
            "run `charmcraft pack` to generate gopkg_*.charm in the working directory."
        )

    app_image = _resolve_app_image()
    # Fresh per-run models default to amd64 pods; match the actual host so
    # the pod can schedule on arm64 dev VMs and amd64 CI runners alike.
    arch = _ARCH_MAP.get(platform.machine(), "amd64")
    await model.set_constraints({"arch": arch})
    application = await model.deploy(
        f"./{charm_file}",
        application_name="gopkg",
        resources={"app-image": app_image},
    )
    try:
        await model.wait_for_idle(apps=[application.name], status="active", timeout=15 * 60)
    except Exception:
        # Surface the real cause in CI logs: spread destroys the model after
        # the run, so this is the only chance to see the hook traceback.
        log = subprocess.run(
            ["juju", "debug-log", "-m", model.name, "--replay", "--no-tail"],
            capture_output=True,
            text=True,
            check=False,
        )
        print("==== juju debug-log (tail) ====")
        print(log.stdout[-8000:])
        raise
    return application
