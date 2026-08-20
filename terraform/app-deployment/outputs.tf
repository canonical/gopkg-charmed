# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "model_uuid" {
  description = "Model UUID used for deployment."
  value       = var.model_uuid
}

output "gopkg_application_name" {
  description = "Name of the deployed gopkg application."
  value       = juju_application.gopkg.name
}

output "gopkg_hostname" {
  description = "Hostname configured for gopkg charm."
  value       = var.gopkg_hostname
}

output "gopkg_app_image" {
  description = "OCI image reference configured for app-image resource."
  value       = var.gopkg_app_image
}

output "ingress_enabled" {
  description = "Whether ingress was deployed and integrated."
  value       = var.deploy_ingress
}

output "ingress_application_name" {
  description = "Name of the deployed ingress application when enabled."
  value       = try(juju_application.ingress[0].name, null)
}
