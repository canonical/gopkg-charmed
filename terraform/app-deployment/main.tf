# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "gopkg" {
  name       = var.gopkg_app_name
  model_uuid = var.model_uuid

  charm {
    name     = var.gopkg_charm_name
    channel  = var.gopkg_charm_channel
    base     = var.gopkg_charm_base
    revision = var.gopkg_charm_revision
  }

  units       = var.gopkg_units
  trust       = var.gopkg_trust
  constraints = var.gopkg_constraints

  config = merge(
    {
      hostname = var.gopkg_hostname
    },
    var.gopkg_extra_config,
  )

  resources = merge(
    {
      "app-image" = var.gopkg_app_image
    },
    var.gopkg_extra_resources,
  )
}

resource "juju_application" "ingress" {
  count      = var.deploy_ingress ? 1 : 0
  name       = var.ingress_app_name
  model_uuid = var.model_uuid

  charm {
    name    = var.ingress_charm_name
    channel = var.ingress_charm_channel
  }

  trust = var.ingress_trust

  config = {
    "service-hostname" = coalesce(var.ingress_service_hostname, var.gopkg_hostname)
    "path-routes"      = var.ingress_path_routes
    "rewrite-enabled"  = var.ingress_rewrite_enabled
  }
}

resource "juju_integration" "ingress_to_gopkg" {
  count      = var.deploy_ingress && var.ingress_endpoint == null && var.gopkg_ingress_endpoint == null ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name = juju_application.ingress[0].name
  }

  application {
    name = juju_application.gopkg.name
  }
}

resource "juju_integration" "ingress_to_gopkg_with_endpoints" {
  count      = var.deploy_ingress && var.ingress_endpoint != null && var.gopkg_ingress_endpoint != null ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = juju_application.ingress[0].name
    endpoint = var.ingress_endpoint
  }

  application {
    name     = juju_application.gopkg.name
    endpoint = var.gopkg_ingress_endpoint
  }
}