# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

# Apply, not plan: only a deployment asks Charmhub for the charms, so a plan
# passes even when no revision exists for a default channel and base. Every
# charm setting stays at the module defaults, so this deploys what a caller
# gets without overriding them.
run "basic_deploy" {
  command = apply

  variables {
    model_uuid        = run.setup_tests.model_uuid
    external_hostname = "gopkg.example.com"
    deploy_ingress    = true
  }

  assert {
    condition     = output.gopkg.app_name == "gopkg"
    error_message = "gopkg app_name did not match expected"
  }

  assert {
    condition     = output.ingress_app_name == "nginx-ingress-integrator"
    error_message = "ingress app_name did not match expected"
  }
}

# A plan is enough here: the run only checks that the integrator is dropped.
run "no_ingress" {
  command = plan

  variables {
    model_uuid     = run.setup_tests.model_uuid
    deploy_ingress = false
  }

  assert {
    condition     = output.ingress_app_name == null
    error_message = "ingress should not be deployed when deploy_ingress is false"
  }
}
