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
        matches = list(glob.glob("gopkg_*.charm"))
        if matches:
            charm_file = matches[0]

    if not charm_file:
        raise FileNotFoundError(
            "No charm file found. Set CHARM_FILE environment variable or "
            "run `charmcraft pack` to generate gopkg_*.charm in the working directory."
        )

    app_image = os.environ.get("APP_IMAGE", "localhost:32000/gopkg:0.1")
    application = await model.deploy(
        f"./{charm_file}",
        application_name="gopkg",
        resources={"app-image": app_image},
    )
    await model.wait_for_idle(apps=[application.name], status="active", timeout=15 * 60)
    return application
