# gopkg-charmed Terraform module

This folder contains a base [Terraform][Terraform] module for the `gopkg-charmed`
charm.

The module uses the [Terraform Juju provider][Terraform Juju provider] to model
the charm deployment onto any Kubernetes environment managed by [Juju][Juju]. It
deploys only the `gopkg-charmed` application — it does not create a Juju model
and does not wire any relations. For a self-contained deployment (gopkg +
ingress + observability wiring), use the [product module](./product/README.md)
instead.

## Module structure

- **main.tf** - Defines the `juju_application` resource for gopkg-charmed.
- **variables.tf** - Inputs for customizing the deployment (charm channel,
  revision, config, constraints, units) and the target model.
- **outputs.tf** - Exposes the application name plus maps of relation endpoint
  names, so calling modules can build `juju_integration` resources without
  hardcoding endpoint names.
- **versions.tf** - Pins the required Terraform and `juju` provider versions.
- **tests/** - `terraform test` suite (`main.tftest.hcl` + a `setup/` helper
  module that creates an ephemeral model). Requires a real Juju controller and
  Kubernetes cloud; intended to run in CI, not locally without infrastructure.

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `app_name` | `string` | `"gopkg"` | Name of the application in the Juju model. |
| `model_uuid` | `string` | *(required)* | UUID of an existing Juju model. This module does not create the model. |
| `base` | `string` | `"ubuntu@24.04"` | Operating system base for the charm. |
| `channel` | `string` | `"latest/edge"` | Charmhub channel to deploy from. |
| `revision` | `number` | `null` | Pin a specific charm revision; `null` uses the latest in `channel`. |
| `config` | `map(string)` | `{}` | Charm config, passed straight through. See [Config options](#config-options). |
| `constraints` | `string` | `""` | Juju constraints string for the application. |
| `units` | `number` | `1` | Number of units to deploy. |

There is deliberately no `resources` input. The `app-image` OCI resource is
published to Charmhub alongside each charm revision, so pinning `revision` also
pins the workload image. Overriding the resource is a local-development concern,
not a deployment one.

## Config options

`config` keys map directly to the charm's config options (see
`app/charm/charmcraft.yaml` in this repository, or
https://charmhub.io/gopkg-charmed/configurations once published):

| Key | Purpose |
|---|---|
| `hostname` | Hostname rendered into import paths and links, injected as `APP_HOSTNAME`. Must match the host clients actually use, or go-import metadata points at the wrong place. |
| `app-port` | Port the application listens on. |
| `metrics-path` | Path where Prometheus metrics are scraped. |
| `metrics-port` | Port where Prometheus metrics are scraped. |
| `app-secret-key` | Shared secret for sessions/CSRF. Prefer `app-secret-key-id`. |
| `app-secret-key-id` | Juju user secret ID holding the application secret key. |

## Outputs

| Name | Description |
|---|---|
| `app_name` | Name of the deployed gopkg application. |
| `requires` | Map of gopkg-charmed's `requires` relations to endpoint names: `ingress`, `logging`. Both optional. |
| `provides` | Map of gopkg-charmed's `provides` relations to endpoint names: `metrics_endpoint` (endpoint name `metrics-endpoint`), `grafana_dashboard` (endpoint name `grafana-dashboard`). Both optional. |

Map keys are snake_case; map values are the literal hyphenated endpoint names
Juju expects.

## External inputs this module does not manage

gopkg-charmed has no required integrations — it runs standalone. For a
deployment reachable from outside the cluster you must additionally provide (or
use the [product module](./product/README.md), which bundles it):

- An ingress provider reachable over the `ingress` interface (optional, needed
  for external HTTP access). See `docs/explanation/ingress.rst` for the
  gopkg-specific requirement that path rewriting stays disabled.
- A Loki-compatible log aggregator over the `logging` (`loki_push_api`)
  interface (optional — gopkg pushes to it, nothing is required for the app to
  function without it).
- Prometheus `metrics-endpoint` and Grafana `grafana-dashboard` integrations are
  optional and provided by gopkg; no external input is needed.

TLS is not handled in-app — ingress terminates it.

## Using the gopkg-charmed base module in higher-level modules

```hcl
resource "juju_model" "my_model" {
  name = "gopkg"
  cloud {
    name = "my-k8s-cloud"
  }
}

module "gopkg" {
  source     = "git::https://github.com/canonical/gopkg-charmed//terraform"
  model_uuid = juju_model.my_model.uuid

  config = {
    "hostname" = "gopkg.example.com"
  }
}

resource "juju_integration" "gopkg_ingress" {
  model_uuid = juju_model.my_model.uuid

  application {
    name     = module.gopkg.app_name
    endpoint = module.gopkg.requires.ingress
  }

  application {
    name     = "nginx-ingress-integrator"
    endpoint = "ingress"
  }
}
```

[Terraform]: https://developer.hashicorp.com/terraform
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
