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
