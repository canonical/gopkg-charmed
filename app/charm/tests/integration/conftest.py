# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm integration tests.

Requires a bootstrapped Juju controller (e.g. the MicroK8s cloud from the
README deployment guide). Configuration via environment variables:

- CHARM_FILE: path to a packed charm (default: first gopkg-k8s_*.charm in CWD)
- APP_IMAGE:  OCI image reference for the app-image resource; overrides
              automatic discovery from ``build/artifacts.build.yaml``
              (default when neither is available: localhost:32000/gopkg:0.1)

Tests use Jubilant: ``gopkg_app`` deploys the charm into pytest-jubilant's
``juju`` model.
"""

import glob
import logging
import os
import platform
from pathlib import Path

import jubilant
import pytest
import yaml

_log = logging.getLogger(__name__)

APP_NAME = "gopkg-k8s"
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


def _find_charm_file() -> str:
    """Return the path of the packed gopkg charm to deploy."""
    charm_file = os.environ.get("CHARM_FILE")
    if not charm_file:
        # charm-ci builds the charm in a separate phase and places it in the
        # project tree, not necessarily the tox working directory - search
        # here first, then recursively from the repository root.
        for pattern in (
            "gopkg-k8s_*.charm",
            "../../gopkg-k8s_*.charm",
            "../../**/gopkg-k8s_*.charm",
        ):
            matches = sorted(glob.glob(pattern, recursive=True))
            if matches:
                charm_file = matches[0]
                break

    if not charm_file:
        raise FileNotFoundError(
            "No charm file found. Set CHARM_FILE environment variable or "
            "run `charmcraft pack` to generate gopkg-k8s_*.charm in the working directory."
        )
    return charm_file


@pytest.fixture(scope="module", name="gopkg_app")
def gopkg_app_fixture(juju: jubilant.Juju) -> str:
    """Deploy gopkg-k8s into the module's model and return its application name."""
    # Fresh per-run models default to amd64 pods; match the actual host so
    # the pod can schedule on arm64 dev VMs and amd64 CI runners alike.
    juju.model_constraints({"arch": _ARCH_MAP.get(platform.machine(), "amd64")})
    juju.deploy(
        Path(_find_charm_file()).resolve(),
        app=APP_NAME,
        resources={"app-image": _resolve_app_image()},
    )
    try:
        juju.wait(lambda status: jubilant.all_active(status, APP_NAME), timeout=15 * 60)
    except Exception:
        # Surface the real cause in CI logs: spread destroys the model after
        # the run, so this is the only chance to see the hook traceback.
        print("==== juju debug-log (tail) ====")
        print(juju.debug_log(limit=200))
        raise
    return APP_NAME
