# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  command = plan

  variables {
    app_name   = "gopkg"
    model_uuid = run.setup_tests.model_uuid
    channel    = "latest/edge"
    revision   = null
  }

  assert {
    condition     = output.app_name == "gopkg"
    error_message = "gopkg app_name did not match expected"
  }

  assert {
    condition     = output.requires.ingress == "ingress"
    error_message = "ingress endpoint name did not match expected"
  }

  assert {
    condition     = output.provides.metrics_endpoint == "metrics-endpoint"
    error_message = "metrics-endpoint endpoint name did not match expected"
  }
}
