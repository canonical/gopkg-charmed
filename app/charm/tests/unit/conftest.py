# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm unit tests."""

import pathlib
import sys
from secrets import token_hex

import pytest
import yaml

PROJECT_ROOT = pathlib.Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "lib"))

import ops.testing  # noqa: E402

# Container is imported from scenario directly: the ops.testing namespace
# exports both API generations and mypy resolves ops.testing.Container to
# the charm-side ops.model.Container instead of the state-transition one.
from scenario import Container  # noqa: E402

from charm import GopkgCharm  # noqa: E402

# The go-framework charmcraft extension injects the workload container, peer
# relation, framework config options and the rotate-secret-key action into
# the packed charm; the source charmcraft.yaml does not contain them. The
# Context must therefore be built with metadata mirroring the packed shape.
CHARM_META = {
    "name": "gopkg",
    "summary": "gopkg.in versioned-import-path service.",
    "description": "Charmed gopkg.in vanity import redirector.",
    "containers": {"app": {"resource": "app-image"}},
    "resources": {
        "app-image": {
            "type": "oci-image",
            "description": "OCI image for the gopkg application.",
        }
    },
    "peers": {"secret-storage": {"interface": "secret-storage"}},
    "requires": {
        "ingress": {"interface": "ingress", "limit": 1, "optional": True},
        "logging": {"interface": "loki_push_api", "optional": True},
    },
    "provides": {
        "metrics-endpoint": {"interface": "prometheus_scrape"},
        "grafana-dashboard": {"interface": "grafana_dashboard"},
    },
}

# Framework options injected at pack time. The packed charm's
# app-secret-key default is a generated random value and paas-charm's
# GoConfig rejects short/empty keys, so mirror that with a random token.
FRAMEWORK_CONFIG_OPTIONS = {
    "app-port": {"type": "int", "default": 8080},
    "metrics-port": {"type": "int", "default": 8080},
    "metrics-path": {"type": "string", "default": "/metrics"},
    "app-secret-key": {"type": "string", "default": token_hex(16)},
}

CHARM_ACTIONS = {"rotate-secret-key": {"description": "Rotate the application secret key."}}


def charm_config_options() -> dict:
    """Return the packed-shape config schema.

    The declared options (hostname) are loaded from the real charmcraft.yaml
    so tests assert against the actual source of truth, then merged with the
    options the go-framework extension injects at pack time.
    """
    charmcraft = yaml.safe_load((PROJECT_ROOT / "charmcraft.yaml").read_text(encoding="utf-8"))
    return {**FRAMEWORK_CONFIG_OPTIONS, **charmcraft["config"]["options"]}


@pytest.fixture(name="ctx")
def ctx_fixture() -> ops.testing.Context:
    """Testing context for GopkgCharm with packed-shape metadata."""
    return ops.testing.Context(
        GopkgCharm,
        meta=CHARM_META,
        config={"options": charm_config_options()},
        actions=CHARM_ACTIONS,
    )


@pytest.fixture(name="base_state")
def base_state_fixture() -> ops.testing.State:
    """Minimal deployable state: workload container and peer relation."""
    return ops.testing.State(
        leader=True,
        containers=[Container(name="app", can_connect=False)],
        relations=[ops.testing.PeerRelation("secret-storage")],
    )
