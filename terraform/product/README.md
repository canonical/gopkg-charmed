# gopkg-charmed product module

This module deploys gopkg together with the charms it needs to be usable
end-to-end: the [base module](../README.md) plus an optional ingress, plus
optional integrations to observability offers.

It does **not** create a Juju model, and it does **not** pin charm revisions.
Revisions are pinned one layer up, in a deployment module (see
[Layering](#layering)).

## Module structure

- **main.tf** - Instantiates the base module and the bundled
  `nginx-ingress-integrator`, and defines every `juju_integration`.
- **variables.tf** - Per-charm configuration objects, `deploy_ingress` toggle,
  and `*_offer_url` inputs for cross-model integrations.
- **outputs.tf** - gopkg's application name and endpoint maps, plus the ingress
  application name when bundled.
- **versions.tf** - Pins the required Terraform and `juju` provider versions.
- **tests/** - `terraform test` suite. Requires a real Juju controller and
  Kubernetes cloud.

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `model_uuid` | `string` | *(required)* | UUID of an existing Juju model. |
| `external_hostname` | `string` | `null` | Public hostname, e.g. `gopkg.example.com`. Required when `deploy_ingress` is true. See [Hostname](#hostname). |
| `gopkg` | `object` | `{}` | gopkg charm settings: `app_name`, `channel`, `revision`, `base`, `config`, `constraints`, `units`. |
| `deploy_ingress` | `bool` | `true` | Deploy the bundled `nginx-ingress-integrator`. |
| `nginx_ingress_integrator` | `object` | `{}` | Ingress charm settings: `app_name`, `channel`, `revision`, `base`, `config`. |
| `logging_offer_url` | `string` | `null` | Offer URL for a Loki provider. Integrated only when set. |
| `metrics_offer_url` | `string` | `null` | Offer URL for a Prometheus scraper. Integrated only when set. |
| `grafana_dashboard_offer_url` | `string` | `null` | Offer URL for a Grafana dashboard provider. Integrated only when set. |

## Outputs

| Name | Description |
|---|---|
| `gopkg` | `{ app_name, requires, provides }` for the gopkg application. |
| `ingress_app_name` | Name of the bundled ingress application, or `null` when `deploy_ingress = false`. |

## Hostname

gopkg's `hostname` charm config and the ingress `service-hostname` describe the
same fact: the host clients use to reach the service. gopkg renders that host
into `go-import` metadata, so if the two drift, import paths point at a host
that does not serve them.

This module therefore threads `external_hostname` into both. An explicit
`hostname` key in `gopkg.config` still wins, if you need them to differ.

## Ingress

The bundled charm is `nginx-ingress-integrator`, deployed with `trust = true`
because it creates Kubernetes Ingress resources on the cluster. It does not
replace the cluster's ingress controller — one must already be running (on
MicroK8s, `sudo microk8s enable ingress`).

Three config values are set by default:

| Key | Default | Why |
|---|---|---|
| `service-hostname` | `external_hostname` | Matches the HTTP `Host` header. |
| `path-routes` | `/` | Exposes all paths, including `/health-check` and package paths such as `/yaml.v2`. |
| `rewrite-enabled` | `"false"` | **Required.** gopkg serves versioned import paths and needs the original path. With rewriting on, every URL answers 307 to `https://labix.org/gopkg.in`. |

`nginx_ingress_integrator.config` is merged *over* these, so overriding
`rewrite-enabled` to `"true"` is possible and will break the deployment. See
`docs/explanation/ingress.rst` for the full explanation.

Set `deploy_ingress = false` when the consuming deployment manages ingress
itself, which is the norm for Platform Engineering environments.

## Observability

COS is not bundled. Instead, pass offer URLs for the pieces you want:

```hcl
logging_offer_url           = "admin/cos.loki-logging"
metrics_offer_url           = "admin/cos.prometheus-scrape"
grafana_dashboard_offer_url = "admin/cos.grafana-dashboards"
```

Each is `null` by default and produces an integration only when set.

## Layering

| Layer | Where | Responsibility |
|---|---|---|
| 1 | [`../`](../README.md) | one `juju_application`, no relations |
| 1.5 | **this module** | companion charms + integrations, behind toggles |
| 2 | `platform-engineering-deployment-modules`, `deployments/gopkg/<cloud>/` | pins channel + revision |
| 3 | `platform-engineering-deployments` | providers, model, hostname, offer URLs |

## Example usage

Self-contained deployment with bundled ingress:

```hcl
resource "juju_model" "gopkg" {
  name = "gopkg"
  cloud {
    name = "my-k8s-cloud"
  }
}

module "gopkg" {
  source     = "git::https://github.com/canonical/gopkg-charmed//terraform/product"
  model_uuid = juju_model.gopkg.uuid

  external_hostname = "gopkg.example.com"

  gopkg = {
    channel  = "latest/edge"
    revision = 12
    units    = 2
  }
}
```

Deployment module usage, where ingress belongs to the environment:

```hcl
module "gopkg" {
  source     = "git::https://github.com/canonical/gopkg-charmed//terraform/product?ref=rev12&depth=1"
  model_uuid = var.model_uuid

  deploy_ingress    = false
  external_hostname = var.external_hostname

  gopkg = {
    channel = "latest/stable"
    # renovate: charm="gopkg-charmed" track="latest" risk="stable" base="24.04" arch="amd64"
    revision = 12
  }
}
```
