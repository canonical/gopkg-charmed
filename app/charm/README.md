[![CharmHub Badge](https://charmhub.io/gopkg-k8s/badge.svg)](https://charmhub.io/gopkg-k8s)
[![Publish charm](https://github.com/canonical/gopkg-charmed/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/publish_charm.yaml)
[![Integration Tests](https://github.com/canonical/gopkg-charmed/actions/workflows/integration-test.yaml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/integration-test.yaml)

# gopkg-k8s

A Juju charm deploying and managing gopkg.in on Kubernetes. gopkg.in is the
service that gives Go programs stable, major-version-specific import paths
such as `gopkg.in/yaml.v2`, resolving each one to the newest matching tag of a
GitHub repository and serving it to the Go tool. It allows for deployment on
many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) to public cloud Kubernetes
offerings.

Like any Juju charm, this charm supports one-line deployment, configuration,
integration, scaling, and more. For gopkg-k8s, this includes:

* Serving `go-import` metadata and package pages under the hostname you
  configure
* Relaying Git transfers from GitHub to the Go tool
* Ingress integration for external HTTP access
* Observability integrations: Prometheus metrics, Loki logs, a Grafana
  dashboard, and alert rules

For information about how to deploy, integrate, and manage this charm, see the
official [gopkg-k8s documentation](https://canonical.com/juju/docs/gopkg-charm/latest/).

## Get started

You need a Juju 3.6 controller on a Kubernetes cloud. The
[tutorial](https://canonical.com/juju/docs/gopkg-charm/latest/tutorials/deploy-and-verify-on-kubernetes/)
sets one up on MicroK8s and builds the charm from source; to deploy the
published charm instead, run:

```bash
juju add-model gopkg-k8s
juju deploy gopkg-k8s --channel latest/edge
```

The service is reachable only inside the cluster until an ingress charm
publishes it. Deploy the
[NGINX ingress integrator](https://charmhub.io/nginx-ingress-integrator),
integrate it, and give both applications the same hostname:

```bash
juju deploy nginx-ingress-integrator --channel latest/stable --trust
juju integrate nginx-ingress-integrator gopkg-k8s
juju config nginx-ingress-integrator service-hostname=gopkg.example.com \
  path-routes=/ rewrite-enabled=false
juju config gopkg-k8s hostname=gopkg.example.com
```

`juju status` reports both applications as `active` when the deployment is
ready.

### Basic operations

#### Configure the hostname

The `hostname` option is the name the service writes into `go-import`
metadata and package links. It must be the name that clients use, so change it
together with the ingress hostname:

```bash
juju config nginx-ingress-integrator service-hostname=go.example.com
juju config gopkg-k8s hostname=go.example.com
```

See [Configure the hostname and check go-import metadata](https://canonical.com/juju/docs/gopkg-charm/latest/how-to/configure-hostname-and-check-go-import/).

#### Serve metrics on a separate port

By default the Prometheus metrics share the application port. To keep them off
the port that ingress publishes:

```bash
juju config gopkg-k8s metrics-port=9102
```

See [Integrate with the Canonical Observability Stack](https://canonical.com/juju/docs/gopkg-charm/latest/how-to/integrate-with-cos/).

You can check out the full list of
[configuration options](https://charmhub.io/gopkg-k8s/configurations) and
[actions](https://charmhub.io/gopkg-k8s/actions) on Charmhub.

## Integrations

This charm can be integrated with other Juju charms and services:

* [NGINX ingress integrator](https://charmhub.io/nginx-ingress-integrator)
  over `ingress` (interface `ingress`): routes external HTTP traffic to the
  service. Required to reach the service from outside the cluster.
* [Loki](https://charmhub.io/loki-k8s) over `logging` (interface
  `loki_push_api`): receives the service's JSON logs and its Loki alert rules.
* [Prometheus](https://charmhub.io/prometheus-k8s) over `metrics-endpoint`
  (interface `prometheus_scrape`): scrapes the service's metrics and loads its
  alert rules.
* [Grafana](https://charmhub.io/grafana-k8s) over `grafana-dashboard`
  (interface `grafana_dashboard`): receives the **gopkg Overview** and
  **Go Operator** dashboards.

You can find the full list of integrations
[here](https://charmhub.io/gopkg-k8s/integrations).

## Learn more

* [Read more](https://canonical.com/juju/docs/gopkg-charm/latest/)
* [Developer documentation](https://canonical.com/juju/docs/gopkg-charm/latest/reference/integrations/):
  endpoints, metrics, logs, and alert rules, for charms that integrate with
  this one
* [Official webpage](https://gopkg.in): the public gopkg.in service and its
  URL and version rules
* [Troubleshooting](https://canonical.com/juju/docs/gopkg-charm/latest/how-to/troubleshoot-deployment/)

## Project and community

* [Issues](https://github.com/canonical/gopkg-charmed/issues)
* [Contributing](https://github.com/canonical/gopkg-charmed/blob/main/CONTRIBUTING.md)
* [Security policy](https://github.com/canonical/gopkg-charmed/blob/main/SECURITY.md)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Licensing and trademark

The charm and the gopkg.in service it operates are distributed under the
[BSD-2-Clause licence](https://github.com/canonical/gopkg-charmed/blob/main/LICENSE).
gopkg.in was created by Gustavo Niemeyer, whose copyright notice is retained.
