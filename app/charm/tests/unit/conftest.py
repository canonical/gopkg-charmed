# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for gopkg charm unit tests."""

import pathlib
import sys
import typing

import pytest

PROJECT_ROOT = pathlib.Path(__file__).parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))
sys.path.append(str(PROJECT_ROOT / "lib"))

import ops.testing  # noqa: E402

from charm import GopkgCharm  # noqa: E402

# The go-framework charmcraft extension injects the workload container, peer
# relation and framework config options into the packed charm's metadata; the
# source charmcraft.yaml does not contain them. The harness must therefore be
# built with metadata mirroring the packed shape.
CHARM_METADATA = """
name: gopkg
summary: gopkg.in versioned-import-path service.
description: Charmed gopkg.in vanity import redirector.
containers:
  app:
    resource: app-image
resources:
  app-image:
    type: oci-image
    description: OCI image for the gopkg application.
peers:
  secret-storage:
    interface: secret-storage
requires:
  ingress:
    interface: ingress
    limit: 1
    optional: true
  logging:
    interface: loki_push_api
    optional: true
provides:
  metrics-endpoint:
    interface: prometheus_scrape
  grafana-dashboard:
    interface: grafana_dashboard
"""


CHARM_ACTIONS = """
rotate-secret-key:
  description: Rotate the application secret key.
"""


@pytest.fixture(name="harness")
def harness_fixture() -> typing.Generator[ops.testing.Harness, None, None]:
    """Testing harness for GopkgCharm with packed-shape metadata.

    Config options are deliberately NOT passed: Harness then auto-loads them
    from the real on-disk charmcraft.yaml, so tests assert against the actual
    declared options (framework options such as app-port exist only in the
    packed charm, injected by the go-framework extension). The
    rotate-secret-key action is likewise pack-time injected and observed by
    paas-charm at init, so it must be provided here.
    """
    harness = ops.testing.Harness(GopkgCharm, meta=CHARM_METADATA, actions=CHARM_ACTIONS)
    yield harness
    harness.cleanup()
