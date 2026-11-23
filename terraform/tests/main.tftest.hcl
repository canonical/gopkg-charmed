# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

# Apply, not plan: only a deployment asks Charmhub for the charm, so a plan
# passes even when no revision exists for the default channel and base. The
# charm's channel, revision and base stay at the module defaults, so this
# deploys what a caller gets without overriding them.
run "basic_deploy" {
  command = apply

  variables {
    app_name   = "gopkg"
    model_uuid = run.setup_tests.model_uuid
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
