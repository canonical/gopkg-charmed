# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

locals {
  # Normalise once so neither the charm config nor the precondition below has to
  # deal with a null hostname.
  external_hostname = var.external_hostname == null ? "" : trimspace(var.external_hostname)

  # gopkg's `hostname` config and the ingress `service-hostname` describe the same
  # fact: the host clients use to reach the service. gopkg renders it into
  # go-import metadata, so if the two drift the import paths point at the wrong
  # host. Thread external_hostname into both; anything set explicitly in
  # var.gopkg.config still wins.
  gopkg_config = merge(
    local.external_hostname == "" ? {} : { hostname = local.external_hostname },
    var.gopkg.config,
  )
}

module "gopkg" {
  source      = "../"
  model_uuid  = var.model_uuid
  app_name    = var.gopkg.app_name
  channel     = var.gopkg.channel
  revision    = var.gopkg.revision
  base        = var.gopkg.base
  config      = local.gopkg_config
  constraints = var.gopkg.constraints
  units       = var.gopkg.units
}

# --- Bundled dependency charms ---

resource "juju_application" "nginx_ingress_integrator" {
  count      = var.deploy_ingress ? 1 : 0
  name       = var.nginx_ingress_integrator.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "nginx-ingress-integrator"
    channel  = var.nginx_ingress_integrator.channel
    revision = var.nginx_ingress_integrator.revision
    base     = var.nginx_ingress_integrator.base
  }

  # The integrator creates Kubernetes Ingress resources on the cluster, which
  # requires trust. It does not replace the cluster's ingress controller.
  trust = true
  units = 1

  config = merge(
    {
      "service-hostname" = local.external_hostname

      # "/" exposes every path, including /health-check and package paths such
      # as /yaml.v2.
      "path-routes" = "/"

      # Must stay false: gopkg serves versioned import paths and needs the
      # original path. With rewriting on, every URL answers 307 to
      # https://labix.org/gopkg.in. See docs/explanation/ingress.rst.
      "rewrite-enabled" = "false"
    },
    var.nginx_ingress_integrator.config,
  )

  lifecycle {
    precondition {
      condition     = local.external_hostname != ""
      error_message = "external_hostname must be set when deploy_ingress is true."
    }
  }
}

# --- Integrations: bundled dependencies ---

resource "juju_integration" "gopkg_ingress" {
  count      = var.deploy_ingress ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.gopkg.app_name
    endpoint = module.gopkg.requires.ingress
  }

  application {
    name     = juju_application.nginx_ingress_integrator[0].name
    endpoint = "ingress"
  }
}

# --- Integrations: external offers (no bundled charm) ---

resource "juju_integration" "gopkg_logging" {
  count      = var.logging_offer_url != null ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.gopkg.app_name
    endpoint = module.gopkg.requires.logging
  }

  application {
    offer_url = var.logging_offer_url
  }
}

resource "juju_integration" "gopkg_metrics" {
  count      = var.metrics_offer_url != null ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.gopkg.app_name
    endpoint = module.gopkg.provides.metrics_endpoint
  }

  application {
    offer_url = var.metrics_offer_url
  }
}

resource "juju_integration" "gopkg_grafana_dashboard" {
  count      = var.grafana_dashboard_offer_url != null ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.gopkg.app_name
    endpoint = module.gopkg.provides.grafana_dashboard
  }

  application {
    offer_url = var.grafana_dashboard_offer_url
  }
}
