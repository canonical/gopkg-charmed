# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_uuid" {
  description = "UUID of the Juju model where the applications will be deployed. The model must already exist; this module does not create one."
  type        = string
}

variable "external_hostname" {
  description = <<-EOT
    Public hostname clients use to reach gopkg, for example "gopkg.example.com".
    Used as the ingress `service-hostname` and threaded into gopkg's `hostname`
    config so go-import metadata matches the host actually serving it. Required
    when deploy_ingress is true. Setting a DNS record for it is out of scope.
  EOT
  type        = string
  default     = null

  validation {
    condition     = var.external_hostname == null || !can(regex("https?://|/", var.external_hostname))
    error_message = "external_hostname must be a bare host or host:port (no scheme or path)."
  }
}

variable "gopkg" {
  description = "gopkg-charmed charm configuration."
  type = object({
    app_name    = optional(string, "gopkg")
    channel     = optional(string, "latest/edge")
    revision    = optional(number, null)
    base        = optional(string, "ubuntu@24.04")
    config      = optional(map(string), {})
    constraints = optional(string, "")
    units       = optional(number, 1)
  })
  default = {}
}

variable "deploy_ingress" {
  description = "Whether to deploy the bundled nginx-ingress-integrator charm. Set to false to manage ingress in the consuming deployment, which is the norm for Platform Engineering environments."
  type        = bool
  default     = true
}

variable "nginx_ingress_integrator" {
  description = <<-EOT
    nginx-ingress-integrator charm configuration (used when deploy_ingress is
    true). Keys in `config` are merged over the module's defaults of
    service-hostname / path-routes / rewrite-enabled. Overriding
    "rewrite-enabled" to "true" breaks gopkg's versioned import paths.
  EOT
  type = object({
    app_name = optional(string, "nginx-ingress-integrator")
    channel  = optional(string, "latest/stable")
    revision = optional(number, null)
    base     = optional(string, null)
    config   = optional(map(string), {})
  })
  default = {}
}

variable "logging_offer_url" {
  description = "Juju offer URL for an existing Loki logging provider. When set, gopkg's logging endpoint is integrated to this offer. Leave null to skip."
  type        = string
  default     = null
}

variable "metrics_offer_url" {
  description = "Juju offer URL for an existing Prometheus metrics scraper. When set, gopkg's metrics-endpoint is integrated to this offer. Leave null to skip."
  type        = string
  default     = null
}

variable "grafana_dashboard_offer_url" {
  description = "Juju offer URL for an existing Grafana dashboard provider. When set, gopkg's grafana-dashboard endpoint is integrated to this offer. Leave null to skip."
  type        = string
  default     = null
}
