# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the gopkg charm shim."""

import json
import pathlib
from secrets import token_hex

import ops.testing
import paas_charm.go
import paas_charm.utils
import yaml

from charm import GopkgCharm


def test_charm_instantiates(ctx: ops.testing.Context, base_state: ops.testing.State) -> None:
    """
    arrange: given a testing context with packed-shape charm metadata
    act: when a config-changed event is dispatched
    assert: the charm initialises without raising and is a paas-charm Go
        charm, so the go-framework contract (Pebble-driven workload, APP_*
        env delivery) applies to it.
    """
    with ctx(ctx.on.config_changed(), base_state) as mgr:
        mgr.run()

        assert isinstance(mgr.charm, GopkgCharm)
        assert isinstance(mgr.charm, paas_charm.go.Charm)


def test_workload_container_defined(
    ctx: ops.testing.Context, base_state: ops.testing.State
) -> None:
    """
    arrange: given an initialised gopkg charm
    act: when the workload container is looked up by the name the
        go-framework extension wires ("app")
    assert: the container exists on the unit.
    """
    with ctx(ctx.on.config_changed(), base_state) as mgr:
        mgr.run()

        container = mgr.charm.unit.get_container("app")

        assert container.name == "app"


def test_hostname_config_default(ctx: ops.testing.Context, base_state: ops.testing.State) -> None:
    """
    arrange: given an initialised gopkg charm with no config overrides
    act: when the hostname option is read
    assert: it defaults to gopkg.in, matching the application's own
        compiled-in fallback.
    """
    with ctx(ctx.on.config_changed(), base_state) as mgr:
        mgr.run()

        hostname = mgr.charm.config["hostname"]

        assert hostname == "gopkg.in"


def test_hostname_config_update(ctx: ops.testing.Context, base_state: ops.testing.State) -> None:
    """
    arrange: given a gopkg charm state carrying a random hostname value
    act: when a config-changed event is dispatched
    assert: the charm observes the updated value, which paas-charm delivers
        to the workload as APP_HOSTNAME.
    """
    hostname = f"{token_hex(8)}.example.com"
    state = ops.testing.State(
        leader=True,
        config={"hostname": hostname},
        containers=base_state.containers,
        relations=base_state.relations,
    )

    with ctx(ctx.on.config_changed(), state) as mgr:
        mgr.run()

        assert mgr.charm.config["hostname"] == hostname


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


def test_custom_cos_assets_are_valid() -> None:
    """
    arrange: given the charm's cos_custom directory with a dashboard and alert
        rules, which paas-charm merges with the go-framework defaults at start-up
    act: when paas-charm validates the directory layout and the assets are parsed
    assert: the layout is accepted, the dashboard binds to the Prometheus
        datasource variable that the Grafana library substitutes, every rule
        file has populated groups, and every Loki rule expression carries the
        topology placeholder the Loki library requires.
    """
    cos_custom = pathlib.Path(__file__).parents[2] / "cos_custom"

    paas_charm.utils.validate_cos_custom_dir(cos_custom)
    dashboard = json.loads(
        (cos_custom / "grafana_dashboards" / "gopkg.json").read_text(encoding="utf-8")
    )
    prometheus_rules = yaml.safe_load(
        (cos_custom / "prometheus_alert_rules" / "gopkg.rule").read_text(encoding="utf-8")
    )
    loki_rules = yaml.safe_load(
        (cos_custom / "loki_alert_rules" / "gopkg.rule").read_text(encoding="utf-8")
    )

    assert dashboard["title"] == "gopkg Overview"
    assert any(item["name"] == "prometheusds" for item in dashboard["templating"]["list"])
    for rules in (prometheus_rules, loki_rules):
        assert rules["groups"]
        assert all(group["rules"] for group in rules["groups"])
    for group in loki_rules["groups"]:
        assert all("%%juju_topology%%" in rule["expr"] for rule in group["rules"])
