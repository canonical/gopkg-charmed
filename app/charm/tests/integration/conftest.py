# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm integration tests.

Requires a bootstrapped Juju controller (e.g. the MicroK8s cloud from the
README deployment guide). Configuration via environment variables:

- CHARM_FILE: path to a packed charm (default: first gopkg_*.charm in CWD)
- APP_IMAGE:  OCI image reference for the app-image resource
              (default: localhost:32000/gopkg:0.1)
"""

import glob
import os
import platform

# python-libjuju types, not ops.model: pytest-operator's ops_test.model is a
# juju.model.Model (which has deploy/wait_for_idle); the similarly named
# charm-side ops.model.Model does not.
import juju.application
import juju.model
import pytest_asyncio
import pytest_operator.plugin


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

    app_image = os.environ.get("APP_IMAGE", "localhost:32000/gopkg:0.1")
    # Fresh per-run models default to amd64 pods; match the actual host so
    # the pod can schedule on arm64 dev VMs and amd64 CI runners alike.
    arch = {"aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine(), "amd64")
    await model.set_constraints({"arch": arch})
    application = await model.deploy(
        f"./{charm_file}",
        application_name="gopkg",
        resources={"app-image": app_image},
    )
    await model.wait_for_idle(apps=[application.name], status="active", timeout=15 * 60)
    return application
