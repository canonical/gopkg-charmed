# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed gopkg application."
  value       = juju_application.gopkg.name
}

output "requires" {
  description = "Map of gopkg-charmed's `requires` relation names to their endpoint names."
  value = {
    ingress = "ingress"
    logging = "logging"
  }
}

output "provides" {
  description = "Map of gopkg-charmed's `provides` relation names to their endpoint names."
  value = {
    metrics_endpoint  = "metrics-endpoint"
    grafana_dashboard = "grafana-dashboard"
  }
}
