# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the gopkg charm shim."""

import pathlib
from secrets import token_hex

import ops.testing
import paas_charm.go
import yaml

from charm import GopkgCharm


def test_charm_instantiates(harness: ops.testing.Harness) -> None:
    """
    arrange: given a testing harness built with packed-shape charm metadata
    act: when the operator framework initialises the charm
    assert: the charm initialises without raising and is a paas-charm Go
        charm, so the go-framework contract (Pebble-driven workload, APP_*
        env delivery) applies to it.
    """
    harness.begin()

    charm = harness.charm

    assert isinstance(charm, GopkgCharm)
    assert isinstance(charm, paas_charm.go.Charm)


def test_workload_container_defined(harness: ops.testing.Harness) -> None:
    """
    arrange: given an initialised gopkg charm
    act: when the workload container is looked up by the name the
        go-framework extension wires ("app")
    assert: the container exists on the unit.
    """
    harness.begin()

    container = harness.charm.unit.get_container("app")

    assert container.name == "app"


def test_hostname_config_default(harness: ops.testing.Harness) -> None:
    """
    arrange: given an initialised gopkg charm with no config overrides
    act: when the hostname option is read
    assert: it defaults to gopkg.in, matching the application's own
        compiled-in fallback.
    """
    harness.begin()

    hostname = harness.charm.config["hostname"]

    assert hostname == "gopkg.in"


def test_hostname_config_update(harness: ops.testing.Harness) -> None:
    """
    arrange: given an initialised gopkg charm and a random hostname
    act: when the hostname option is updated
    assert: the charm observes the updated value, which paas-charm delivers
        to the workload as APP_HOSTNAME.
    """
    hostname = f"{token_hex(8)}.example.com"
    harness.begin()

    harness.update_config({"hostname": hostname})

    assert harness.charm.config["hostname"] == hostname


def test_charmcraft_declares_go_framework_contract() -> None:
    """
    arrange: given the charm's source charmcraft.yaml
    act: when the extension and config declarations are parsed
    assert: the go-framework extension is enabled and the hostname option is
        declared as a string defaulting to gopkg.in, so the packed charm
        delivers APP_HOSTNAME to the workload.
    """
    charmcraft_path = pathlib.Path(__file__).parents[2] / "charmcraft.yaml"

    charmcraft = yaml.safe_load(charmcraft_path.read_text(encoding="utf-8"))

    assert "go-framework" in charmcraft["extensions"]
    hostname_option = charmcraft["config"]["options"]["hostname"]
    assert hostname_option["type"] == "string"
    assert hostname_option["default"] == "gopkg.in"
