# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_uuid" {
  description = "UUID of an existing Juju model where the applications will be deployed."
  type        = string

  validation {
    condition     = length(trimspace(var.model_uuid)) > 0
    error_message = "model_uuid must not be empty."
  }
}

variable "gopkg_app_name" {
  description = "Application name for the gopkg charm deployment."
  type        = string
  default     = "gopkg"
}

variable "gopkg_charm_name" {
  description = "Charm name to deploy for gopkg."
  type        = string
  default     = "gopkg-charmed"
}

variable "gopkg_charm_channel" {
  description = "Charmhub channel used to deploy gopkg."
  type        = string
  default     = "latest/edge"
}

variable "gopkg_charm_revision" {
  description = "Optional pinned charm revision for deterministic deployments."
  type        = number
  default     = null
}

variable "gopkg_charm_base" {
  description = "Optional base to deploy the charm on (for example ubuntu@24.04)."
  type        = string
  default     = "ubuntu@24.04"
}

variable "gopkg_units" {
  description = "Number of gopkg units to deploy."
  type        = number
  default     = 1
}

variable "gopkg_hostname" {
  description = "Hostname rendered by gopkg into links and go-import metadata."
  type        = string
  default     = "gopkg.in"

  validation {
    condition     = !can(regex("https?://|/", var.gopkg_hostname))
    error_message = "gopkg_hostname must be a bare host or host:port (no scheme or path)."
  }
}

variable "gopkg_app_image" {
  description = "OCI image reference for the charm app-image resource (prefer digest pinning)."
  type        = string
  default     = "ghcr.io/minulo/gopkg:latest"

  validation {
    condition     = length(trimspace(var.gopkg_app_image)) > 0
    error_message = "gopkg_app_image must not be empty."
  }
}

variable "gopkg_trust" {
  description = "Whether to deploy gopkg with trust enabled."
  type        = bool
  default     = false
}

variable "gopkg_constraints" {
  description = "Optional Juju constraints for the gopkg application."
  type        = string
  default     = null
}

variable "gopkg_extra_config" {
  description = "Additional charm config key/value pairs to merge with hostname."
  type        = map(string)
  default     = {}
}

variable "gopkg_extra_resources" {
  description = "Additional charm resources to merge with app-image."
  type        = map(string)
  default     = {}
}

variable "deploy_ingress" {
  description = "Whether to deploy nginx-ingress-integrator and relate it to gopkg."
  type        = bool
  default     = true
}

variable "ingress_app_name" {
  description = "Application name for ingress deployment."
  type        = string
  default     = "nginx-ingress-integrator"
}

variable "ingress_charm_name" {
  description = "Ingress charm name."
  type        = string
  default     = "nginx-ingress-integrator"
}

variable "ingress_charm_channel" {
  description = "Ingress charm channel."
  type        = string
  default     = "latest/stable"
}

variable "ingress_trust" {
  description = "Whether ingress is deployed with trust enabled."
  type        = bool
  default     = true
}

variable "ingress_service_hostname" {
  description = "Hostname used by ingress for host-based routing. Defaults to gopkg_hostname when null."
  type        = string
  default     = null
}

variable "ingress_path_routes" {
  description = "Path routes passed to ingress charm config."
  type        = string
  default     = "/"
}

variable "ingress_rewrite_enabled" {
  description = "Ingress rewrite-enabled config. Keep false for gopkg to avoid redirect issues."
  type        = bool
  default     = false
}

variable "ingress_endpoint" {
  description = "Optional explicit ingress endpoint name for the relation."
  type        = string
  default     = null

  validation {
    condition = (
      var.ingress_endpoint == null && var.gopkg_ingress_endpoint == null
      ) || (
      var.ingress_endpoint != null && var.gopkg_ingress_endpoint != null
    )
    error_message = "ingress_endpoint and gopkg_ingress_endpoint must be set together, or both left null."
  }
}

variable "gopkg_ingress_endpoint" {
  description = "Optional explicit gopkg endpoint name for the relation."
  type        = string
  default     = null
}
