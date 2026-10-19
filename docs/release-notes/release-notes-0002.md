---
myst:
  html_meta:
    "description lang=en": "Release notes for gopkg-k8s revisions 1-8: new features, bug fixes, and breaking changes."
---

(release_notes_release_notes_0002)=

# gopkg-k8s release notes – latest/edge

These release notes cover new features and changes in gopkg-k8s for
revisions 1-8.

This is the first release since the {ref}`initial documentation baseline <release_notes_release_notes_0001>`. The charm is now published to the latest/edge channel on every push to main, and it integrates with the Canonical Observability Stack through metrics, structured logs, a Grafana dashboard, and alert rules. The documentation gained a rewritten tutorial around the published charm, guides for upgrading the charm and for integrating with COS Lite, and Terraform modules for deploying with Juju.

Main features:

* Added a how-to guide for upgrading the charm.
* Published the charm to the latest/edge channel on every push to main.
* Added metrics, structured logs, a Grafana dashboard, and alert rules for the Canonical Observability Stack.
* Rewrote the tutorial around the published charm.

Main bug fixes:

* Bounded the HTTP method label on request metrics.

See the {ref}`release policy and schedule <release_notes_index>`.

## Requirements and compatibility

<!-- Review: add upgrade instructions here if this release needs them. -->

The charm operates gopkg.in 0.1.

The table below shows the required or supported versions of the software
necessary to operate the charm.

| Software   | Required version |
|------------|------------------|
| Juju       | 3.6 |
| Kubernetes | MicroK8s 1.36 |
| Ubuntu     | 24.04 |

## Updates

The following major and minor features were added in this release.

### Added a how-to guide for upgrading the charm

The new guide, How to upgrade the charm, explains what `juju refresh` does for gopkg-k8s (a revision carries the charm and its app-image resource, and there is no state to migrate), how to compare the running revision with the one the channel offers, how to wait for Juju to replace the pod, how to verify the service through ingress afterwards, and how to roll back. It states the cost of an upgrade up front, which is that requests through ingress fail for one to four minutes until the new unit publishes its address. A third documentation-test chain runs the guide on every change.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/53)

### Folded the environment-setup guide into the tutorial

The tutorial now installs Juju and MicroK8s itself and carries its own prerequisites, so the environment-setup guide is gone from the how-to section; its full version, with the build tooling, is the contributor page "Set up a development environment". Both documentation-test chains start at the tutorial. The old address redirects.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/47)

### Named COS Lite in the observability guide

The observability guide deploys Prometheus, Loki, and Grafana, which make up COS Lite, but called them the Canonical Observability Stack. The guide, its entries in the how-to index and on the home page, and the troubleshooting entry for a blocked charm now say COS Lite, and the guide notes that the full COS keeps metrics in Mimir, fed by an OpenTelemetry Collector, so its steps do not apply to the full COS as written.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/55)

### Fetched a module with the Go tool at the end of the tutorial

The tutorial now ends by switching the deployment to the gopkg.in name, pointing that name at the machine, and building a Go program whose gopkg.in/yaml.v2 import the Go tool fetches through the deployment, with the service's request counters as the proof. It explains why the name has to be gopkg.in, because a module's import path must match the module line of its go.mod, and installs the go snap and git for the step.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/46)

### Explained what gopkg.in is for and who should run a deployment

The charm's description, both READMEs, the documentation home page and the tutorial introduction now say what the gopkg.in service does for a Go program, that Canonical maintains the charm to run the public gopkg.in, and that a deployment serves imports of the hostname it is configured with, so a copy of your own is a mirror or a private import domain rather than a replacement for the public service.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/42)

### Published the charm to the latest/edge channel on every push to main

Added a publication workflow that, after every push to main, takes the charm and rock built and tested by the most recent successful integration-test run for that source tree, uploads the rock as the app-image resource, and releases the charm to the latest/edge channel declared in artifacts.yaml. The workflow can also be started by hand to publish to another channel, such as promoting a tested revision to latest/stable, or to validate without uploading. The integration tests now run on every push to main as well, so publication always has a tested tree to ship.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/35)

### Added integration tests for every charm endpoint

Added a test module that integrates each of the charm's endpoints with a published counterpart and checks that both applications settle in active. The ingress endpoint is tested with nginx-ingress-integrator, including a health check routed through the ingress controller; logging with loki-k8s; metrics-endpoint with prometheus-k8s, including a check that Prometheus registers a scrape target for the charm; and grafana-dashboard with grafana-k8s. The observability charms are published for amd64 only, so those tests are skipped on arm64 hosts.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/35)

### Added metrics, structured logs, a Grafana dashboard, and alert rules for the Canonical Observability Stack

The service now exposes Prometheus metrics for requests, upstream GitHub and godoc.org calls, the refs cache, and git upload-pack traffic, at the framework's metrics path on the application port or on a separate port when the metrics-port option differs, which keeps the endpoint off the hostname ingress publishes. Logs are structured JSON records that Pebble forwards to Loki. The charm ships a gopkg Overview Grafana dashboard and Prometheus and Loki alert rules for scrape failures, server errors, latency, GitHub failures, application termination, and error-log spikes. A new how-to guide covers integrating with the Canonical Observability Stack, and the reference documents the endpoints, metrics, logs, and alert rules.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/35)

### Built and published artifacts for AMD64 only

The build plan listed an arm64 rock without the runner labels that would place it on an arm64 machine, so that job ran on an amd64 runner, built a second amd64 rock, and overwrote the amd64 image tag. No arm64 rock was ever produced. The build plan now declares amd64 alone, which halves the rock build and removes the race on the image tag. The rock and charm recipes still declare arm64, so building locally on an arm64 machine works as the guides describe.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/35)

### Prepared the charm's metadata and documentation for the Charmhub listing review

The charm's links now include a website and give the source and issues links as single URLs, which is the form the Charmhub listing review checks. The explanation of the gopkg.in service gained a section on how a deployment differs from the public service, covering TLS termination at the ingress, configuration through charm options, the in-memory references cache, and the published architecture. The tutorial now says how to deploy the published charm from Charmhub instead of building it. The traffic loop in the observability guide now ends by itself with a success status, so the commands after it run. The charm now carries a README, so its Charmhub page describes what it does, how to deploy and integrate it, and where the documentation is; the repository README was rewritten to point at the charm README and the documentation instead of repeating them.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/35)

### Led the home page with a table of domains

The home page's "In this documentation" section is now a table with one row per domain of concern (getting started, deployment, operations, versioned import paths, design, security, development), each linking to the pages and sections that cover it, in place of the four Diátaxis cards. "How this documentation is organized" describes each Diátaxis section by its purpose.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/51)

### Added Terraform modules for deploying gopkg with Juju

Added a base Terraform module at terraform/ that deploys the gopkg-k8s application on its own, exposing the charm's requires and provides relation endpoint names so calling modules can build integrations without hardcoding them. Added a product module at terraform/product/ that composes the base module with an optional nginx-ingress-integrator deployment, preconfigured with the path routing and disabled rewriting that gopkg's versioned import paths require, plus optional integrations to existing Loki, Prometheus, and Grafana offers. Neither module creates a Juju model or pins a charm revision, so both stay reusable across environments. Replaces the previous terraform/app-deployment module, whose hostname, container image, and ingress deployment were environment-specific and are now supplied by the caller. Added a CI workflow that checks formatting, lints, and runs the Terraform test suites for both modules against a Juju controller.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/32)

### Moved the contributor pages out of the how-to and reference sections and dropped the generic charms-and-rocks page

The CI workflows reference and the guide to running the Juju integration suite locally are now in the contributor section, and the generic introduction to Juju, charms and rocks is replaced by links to the Juju, Charmcraft and Rockcraft documentation. Old addresses redirect.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/45)

### Moved the build-from-source failures to a contributor troubleshooting page

The four troubleshooting entries that only apply when building the rock and the charm from source (the local registry refusing connections, a build that does not match the machine's architecture, a rock build tripping on Python files from another OS, tox in a mounted checkout) now live on "Troubleshoot the development environment" under Contribute. "How to troubleshoot deployment issues" keeps the Juju, ingress, HTTPS, and observability entries for operators of the published charm. The Contribute page now lists its pages under a documentation path and a code path, and says that documentation changes need the full development environment only when a command builds, deploys, or changes the running service.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/52)

### Rewrote the tutorial around the published charm

The tutorial deploys gopkg-k8s from Charmhub's latest/edge channel, which carries the charm and its app-image resource, instead of building the rock and the charm from source first. It needs an AMD64 machine, because the published charm is AMD64 only. Building from source, which also works on ARM64, moved to the contributor guide. The documentation tests therefore exercise the published charm; the integration tests still build and test the source tree.
<!-- Review: add context for this entry if needed. -->

Relevant links:

* [PR](https://github.com/canonical/gopkg-charmed/pull/43)

## Bug fixes

* Bounded the HTTP method label on request metrics ([PR](https://github.com/canonical/gopkg-charmed/pull/40)).
* Pointed the documentation links at the public documentation site ([PR](https://github.com/canonical/gopkg-charmed/pull/41)).

## Known issues

<!-- Review: list the most important unresolved issues with links, or keep
"No known issues." -->

No known issues.

## Thanks to our contributors

[minulo](https://github.com/minulo)
