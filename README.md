[![CharmHub Badge](https://charmhub.io/gopkg-k8s/badge.svg)](https://charmhub.io/gopkg-k8s)
[![Charm CI](https://github.com/canonical/gopkg-charmed/actions/workflows/test.yaml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/test.yaml)
[![Go tests](https://github.com/canonical/gopkg-charmed/actions/workflows/go-tests.yaml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/go-tests.yaml)
[![Integration Tests](https://github.com/canonical/gopkg-charmed/actions/workflows/integration-test.yaml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/integration-test.yaml)
[![Documentation tests](https://github.com/canonical/gopkg-charmed/actions/workflows/documentation-tests.yml/badge.svg)](https://github.com/canonical/gopkg-charmed/actions/workflows/documentation-tests.yml)

# gopkg-k8s

The gopkg.in service and the Juju charm that operates it on Kubernetes, in one
repository. gopkg.in gives Go programs stable, major-version-specific import
paths such as `gopkg.in/yaml.v2`; the source was imported from
[niemeyer/gopkg](https://github.com/niemeyer/gopkg) and is maintained here.

Canonical maintains this charm to run the public gopkg.in service. The
service writes the hostname it is configured with into its `go-import`
metadata, so a deployment serves imports of *that* hostname, not of
`gopkg.in`: code that already imports `gopkg.in/...` keeps using the public
service. Run your own copy to mirror gopkg.in inside a network that cannot
reach it, or to offer versioned import paths for GitHub repositories under
your own domain.

Like any Juju charm, `gopkg-k8s` supports one-line deployment, configuration,
integration, scaling, and more. For gopkg-k8s, this includes:

* Serving `go-import` metadata and package pages under the hostname you
  configure
* Ingress integration for external HTTP access
* Observability integrations: Prometheus metrics, Loki logs, a Grafana
  dashboard, and alert rules

For information about how to deploy, integrate, and manage the charm, see the
official [gopkg-k8s documentation](https://canonical.com/juju/docs/gopkg-charm/latest/)
and the [charm's README](app/charm/README.md), which is what
[Charmhub](https://charmhub.io/gopkg-k8s) shows.

## Repository layout

| Path | Contents |
| --- | --- |
| [app/](app/) | The Go service: source, `go.mod`, and tests. Also the 12-factor pipeline: [app/rockcraft.yaml](app/rockcraft.yaml) builds the rock (OCI image) with Rockcraft's Go framework extension. |
| [app/charm/](app/charm/) | The `gopkg-k8s` charm, built with Charmcraft's Go framework extension: [charmcraft.yaml](app/charm/charmcraft.yaml), source, unit and integration tests. |
| [docs/](docs/) | The documentation (Sphinx, Diátaxis): tutorial, how-to guides, reference, explanation, and release notes. |
| [terraform/](terraform/) | Terraform modules for deploying the charm with the Juju provider. |
| [tests/spread/documentation/](tests/spread/documentation/) | Spread tasks that execute the documentation's commands on a bare system. |
| [.github/workflows/](.github/workflows/) | CI: lint and unit tests, Go tests, integration tests, documentation tests, and publication to Charmhub. |

## Get started

### Deploy the charm

With a Juju 3.6 controller on a Kubernetes cloud:

```bash
juju add-model gopkg-k8s
juju deploy gopkg-k8s --channel latest/edge
```

The [charm's README](app/charm/README.md) continues with ingress and the
hostname, and the
[tutorial](https://canonical.com/juju/docs/gopkg-charm/latest/tutorials/deploy-and-verify-on-kubernetes/)
walks through the same deployment from source on MicroK8s, including building
the rock and the charm.

### Run the service locally

The service needs only a Go toolchain (1.21 or later, see
[app/go.mod](app/go.mod)). Configuration comes from the environment:

```bash
cd app
go test ./... && go build -o gopkg .
APP_PORT=8080 APP_HOSTNAME=localhost ./gopkg
# in another terminal:
curl localhost:8080/health-check        # -> ok
```

`APP_PORT` and `APP_HOSTNAME` are the settings the charm passes to the
workload; the `-http` and `-hostname` flags override them. Invalid values fail
at startup with a one-line error. TLS is not handled in the service: ingress
terminates it. Prometheus metrics are served at `APP_METRICS_PATH` (default
`/metrics`) on the application port, or on `APP_METRICS_PORT` when it is set;
logs are JSON lines on standard output.

### Build and test

[CONTRIBUTING.md](CONTRIBUTING.md) lists the checks every change runs, and the
documentation's contribution guides cover
[the code](docs/contribute/improve-code.rst) and
[the documentation](docs/contribute/improve-documentation.rst) step by step.

## Terraform module

A reusable [Terraform](https://developer.hashicorp.com/terraform) module for
deploying the charm with the
[Juju Terraform provider](https://registry.terraform.io/providers/juju/juju/latest/docs)
is in [terraform/](terraform/README.md) (application only) and
[terraform/product/](terraform/product/README.md) (model, application,
ingress, and observability wiring).

## Documentation

The documentation is in [docs/](docs/), based on the Canonical starter pack
and published at
[canonical.com/juju/docs/gopkg-charm](https://canonical.com/juju/docs/gopkg-charm/latest/).
It follows the [Diátaxis](https://diataxis.fr/) approach.

To preview it locally before submitting changes:

```bash
cd docs
make run
```

GitHub runs automatic checks on the documentation for spelling, links, and
inclusive language, and executes the tutorial and how-to guides on a fresh
system. Run the static checks locally with:

```bash
make spelling
make linkcheck
make woke
make lint-md
```

## Project and community

* [Issues](https://github.com/canonical/gopkg-charmed/issues)
* [Contributing](CONTRIBUTING.md)
* [Security policy](SECURITY.md)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)

## Licensing and trademark

The charm and the gopkg.in service are distributed under the
[BSD-2-Clause licence](LICENSE). gopkg.in was created by Gustavo Niemeyer,
whose copyright notice is retained.
