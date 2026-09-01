# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "gopkg" {
  description = "gopkg application name and relation endpoint names."
  value = {
    app_name = module.gopkg.app_name
    requires = module.gopkg.requires
    provides = module.gopkg.provides
  }
}

output "ingress_app_name" {
  description = "Name of the deployed nginx-ingress-integrator application, if bundled (deploy_ingress = true)."
  value       = one(juju_application.nginx_ingress_integrator[*].name)
}
