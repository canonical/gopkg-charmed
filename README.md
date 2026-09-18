# gopkg.in — Stable APIs for the Go language

See [http://gopkg.in](http://gopkg.in).

## About this repository

This repository hosts the source of the gopkg.in service, imported as a
snapshot from [niemeyer/gopkg](https://github.com/niemeyer/gopkg), and is
the operated source of truth for the service going forward.

## Repository layout

The service is scoped to the [app/](app/) folder, which is the permanent Go
project root and the home of the entire 12-factor pipeline: the Go source and
`go.mod` live there, alongside the rock (`app/rockcraft.yaml`) and charm
(`app/charm/`) — both built with the 12-factor `go-framework` extensions for
Rockcraft and Charmcraft.

The repository root is deliberately reserved for sibling concerns that need
separation from the app: `docs/` (release-notes tooling, existing), and in
the future `terraform/` (deployment module) and `tests/` (integration
tests).

## Quickstart: run locally

### Prerequisites

The app itself needs only a **Go toolchain ≥ 1.21** (see `app/go.mod`):

```bash
# macOS
brew install go
# Ubuntu/Debian
sudo snap install go --classic
# verify
go version
```

Go downloads and verifies the module dependencies automatically on the
first build (from `go.mod`/`go.sum`; network access required once — they
are cached afterwards). Nothing else is needed: no database, no config
files. Running the charm test suites needs Python 3.12 and
[tox](https://tox.wiki) (`pipx install tox`), and deploying needs the
tooling in the next section — neither is required just to run the app.

### Build, test, run

```bash
cd app
go test ./... && go build -o gopkg .
APP_PORT=8080 APP_HOSTNAME=localhost ./gopkg
# in another terminal:
curl localhost:8080/health-check        # -> ok
```

Config comes from the environment (`APP_PORT`, `APP_HOSTNAME`); explicit flags
(`-http`, `-hostname`) override it. Invalid values fail at startup with a
one-line error. TLS is not handled in-app — ingress terminates it. Prometheus
metrics are served at `APP_METRICS_PATH` (default `/metrics`) on the app port,
or on a separate `APP_METRICS_PORT` when one is set; logs are JSON lines on
standard output.

## Deploying as a 12-factor charm

End-to-end: build the rock (OCI image) and charm from this repository and
deploy them to a local MicroK8s cloud with Juju. Written for a macOS host
using Multipass; on a Linux amd64 host, skip step 0 and read `arm64` as
`amd64` throughout.

### 0. VM setup (macOS host)

Rockcraft and Charmcraft are Linux snaps — use a Multipass VM and **mount** the
repo into it (no GitHub auth needed in the VM; build artifacts land back on the
host):

```bash
multipass launch 24.04 --cpus 4 --disk 50G --memory 8G --name charm-dev
multipass mount /path/to/gopkg-charmed charm-dev:/home/ubuntu/gopkg-charmed
multipass shell charm-dev
```

Notes:

- 8G memory recommended: with 4G, the Juju controller plus two charms can leave
  the scheduler refusing pods (`Pending`, "Insufficient memory").
- Mount under `/home/ubuntu/` — snap-confined tools may not read paths outside
  `/home`.
- On Apple Silicon the VM (and everything built in it) is **arm64**. Rocks and
  charms built here run in the VM's MicroK8s; an amd64 target needs an amd64
  build host or CI.

### 1. One-time toolchain setup (inside the VM)

```bash
sudo snap install curl
sudo snap install lxd
sudo snap install rockcraft --classic
sudo snap install charmcraft --classic
sudo snap install juju --channel 3/stable
sudo snap install microk8s --channel 1.36-strict/stable
lxd init --auto        # rockcraft/charmcraft build inside LXD; init is required once
sudo adduser $USER snap_microk8s
exit                   # re-enter with `multipass shell charm-dev` to pick up the group
```

> Do **not** chain `newgrp` with further pasted commands — it starts a new
> shell and swallows every line after it. Log out and back in instead, then:

```bash
microk8s status --wait-ready
sudo microk8s enable dns hostpath-storage registry ingress
microk8s status --wait-ready
mkdir -p ~/.local/share
juju bootstrap microk8s dev
```

### 2. Build and push the rock

`app/rockcraft.yaml` is committed. Check that `platforms:` matches the build
machine (`dpkg --print-architecture`), then:

```bash
cd ~/gopkg-charmed/app
ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false \
  --dest-no-creds \
  oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
  docker://localhost:32000/gopkg:0.1
```

The first pack takes several minutes (downloads the build base into LXD);
subsequent packs are fast. Verify the push from the same VM shell:
`curl http://localhost:32000/v2/gopkg/tags/list`.

### 3. Build the charm

`app/charm/` is committed (including vendored `lib/charms/*` — that is the
charm-ecosystem convention). Check `platforms:` in `charmcraft.yaml` matches
the build machine (a mismatch fails with "No build matches the current
execution environment"), then:

```bash
cd ~/gopkg-charmed/app/charm
CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
```

### 4. Deploy

```bash
juju add-model gopkg-k8s
juju set-model-constraints arch=$(dpkg --print-architecture)
# ^ REQUIRED: without it Juju defaults pods to an amd64 nodeSelector, which can
#   never schedule on an arm64 node — pods stay Pending with no events.
#   Constraints bind at deploy time; set them BEFORE deploying.

juju deploy ./gopkg-k8s_*.charm gopkg-k8s --resource app-image=localhost:32000/gopkg:0.1
juju deploy nginx-ingress-integrator --channel=latest/stable --trust
juju integrate nginx-ingress-integrator gopkg-k8s

# rewrite-enabled=false is CRITICAL: the default rewrites every request path
# to "/", so the app answers its root redirect (307) for every URL.
juju config nginx-ingress-integrator \
  service-hostname=gopkg.example.com path-routes=/ rewrite-enabled=false
juju config gopkg-k8s hostname=gopkg.example.com

juju status --watch 2s    # first deploy: 5-15 min to active/idle is normal
```

Two hostname settings exist — do not conflate them, and keep them equal:

- `nginx-ingress-integrator service-hostname` — which `Host:` the ingress
  **routes** to the app.
- `gopkg-k8s hostname` (→ `APP_HOSTNAME`) — what the app **renders** in pages and
  `go-import` meta tags. `go get` rejects a meta tag whose import prefix
  differs from the host it asked, so this must be the routed name.

### 5. Verify

```bash
curl -sw '\nHTTP %{http_code}\n' http://gopkg.example.com/health-check \
  --resolve gopkg.example.com:80:127.0.0.1
# expect: ok / HTTP 200   (note: the body is "ok" with no trailing newline —
# without -w it can vanish against the shell prompt)

curl -s "http://gopkg.example.com/yaml.v2?go-get=1" \
  --resolve gopkg.example.com:80:127.0.0.1
# expect: HTML containing a go-import meta tag for gopkg.example.com/yaml.v2

# Config change without rebuild (the app gets it as APP_HOSTNAME); change
# both names together so the metadata keeps matching the routed host:
juju config nginx-ingress-integrator service-hostname=staging.example.com
juju config gopkg-k8s hostname=staging.example.com
```

### Troubleshooting

| Symptom                                                                         | Cause                         | Fix                                                                                                |
| ------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| `rockcraft pack`: "LXD has not been properly initialized"                       | LXD never initialized         | `lxd init --auto`                                                                                  |
| `charmcraft pack`: "No build matches the current execution environment"         | `platforms:` ≠ build arch     | set `platforms:` to `dpkg --print-architecture`                                                    |
| Pods `Pending`, `describe pod` shows `Node-Selectors: kubernetes.io/arch=amd64` | model constraints unset       | `juju set-model-constraints arch=…`, remove and redeploy apps                                      |
| Pods `Pending`, "Insufficient memory"                                           | VM too small                  | `multipass stop charm-dev && multipass set local.charm-dev.memory=8G && multipass start charm-dev` |
| Integrator `blocked`: "service-hostname is not set"                             | its config, not the app's     | `juju config nginx-ingress-integrator service-hostname=…`                                          |
| Every URL answers 307 → `https://labix.org/gopkg.in`                            | ingress path rewrite          | `juju config nginx-ingress-integrator rewrite-enabled=false`                                       |
| curl prints nothing but exit 0                                                  | body without trailing newline | add `-w '\n%{http_code}\n'`                                                                        |
| COS charm `blocked`: "Kubernetes resources patch failed: Unauthorized"          | Juju/COS token race, no retry | `juju remove-application <app> --destroy-storage --force --no-prompt`, redeploy, re-integrate      |
| `kubectl describe pod -n gopkg-k8s gopkg-k8s-0`                         | —                             | names the exact scheduling blocker                                                                 |

## Charmhub listing review

`gopkg-k8s` is published on [Charmhub](https://charmhub.io/gopkg-k8s)
but not yet *listed* (it does not appear in searches). Listing requires a
lightweight review, requested as a
[listing request issue](https://github.com/canonical/charmhub-listing-review/issues/new?template=listing-request.yml)
in `canonical/charmhub-listing-review`. The criteria are the
[Charmhub public listing requirements](https://canonical.com/juju/docs/ops/latest/howto/make-your-charm-discoverable/)
from the Ops documentation; the original
[Reviewing charms](https://discourse.charmhub.io/t/reviewing-charms/11698)
Discourse post describes the same prerequisites in their earlier form. One
issue covers exactly one charm, and the review runs against `main`.

### Review prerequisites and where they live

| Prerequisite | In this repository |
| --- | --- |
| Charm name and store page | `gopkg-k8s` on [charmhub.io/gopkg-k8s](https://charmhub.io/gopkg-k8s); metadata, links and icon in [app/charm/charmcraft.yaml](app/charm/charmcraft.yaml) and [app/charm/icon.svg](app/charm/icon.svg). Publisher: Platform Engineering (Canonical). |
| Source repository | [github.com/canonical/gopkg-charmed](https://github.com/canonical/gopkg-charmed); the charm directory is `app/charm`. |
| Demo or tutorial | [Deploy and verify on Kubernetes](docs/tutorials/deploy-and-verify-on-kubernetes.rst), executed in CI by [documentation-tests.yml](.github/workflows/documentation-tests.yml). |
| Coding conventions in CI | [test.yaml](.github/workflows/test.yaml) (ruff, mypy, codespell, pytest via [app/charm/tox.ini](app/charm/tox.ini)), [go-tests.yaml](.github/workflows/go-tests.yaml) (gofmt, vet, race tests), [.pre-commit-config.yaml](.pre-commit-config.yaml) (docs). |
| Unit tests | Charm: [app/charm/tests/unit](app/charm/tests/unit), run by `tox -e unit`. Service: `app/*_test.go`, run by `go test -race`. Results: [Charm CI runs](https://github.com/canonical/gopkg-charmed/actions/workflows/test.yaml), [Go test runs](https://github.com/canonical/gopkg-charmed/actions/workflows/go-tests.yaml). |
| Installation and integration tests | [app/charm/tests/integration](app/charm/tests/integration), run through [integration-test.yaml](.github/workflows/integration-test.yaml) (charm-ci, spread) on every pull request, every push to `main`, and weekly. `test_charm.py` deploys the charm to `active` and checks the health endpoint; `test_integrations.py` integrates each endpoint (`ingress`, `logging`, `metrics-endpoint`, `grafana-dashboard`) with a published counterpart. Results: [Integration Tests runs](https://github.com/canonical/gopkg-charmed/actions/workflows/integration-test.yaml). |
| Release automation to an unstable channel | [publish_charm.yaml](.github/workflows/publish_charm.yaml), calling charm-ci `publish-artifacts.yml` on every push to `main`; the channel comes from [artifacts.yaml](artifacts.yaml) (`latest/edge`). Results: [Publish charm runs](https://github.com/canonical/gopkg-charmed/actions/workflows/publish_charm.yaml). |
| Usage documentation | [docs/](docs/): tutorial, how-to guides, reference and explanation, built with Sphinx ([.readthedocs.yaml](.readthedocs.yaml)). The published URL is the `documentation` link in `charmcraft.yaml`. |
| Contribution documentation | [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contribute/](docs/contribute/). |
| Licence statement | [LICENSE](LICENSE) (BSD-2-Clause, upstream gopkg.in notice retained) and [app/charm/LICENSE](app/charm/LICENSE). |
| Security statement | [SECURITY.md](SECURITY.md). |
| Dependency pinning and updates | Runtime dependencies and `requires-python` in [app/charm/pyproject.toml](app/charm/pyproject.toml), resolved to exact versions in [app/charm/uv.lock](app/charm/uv.lock); [app/charm/requirements.txt](app/charm/requirements.txt) mirrors the list for the charm build. Automated updates via [renovate.json](renovate.json). |
| Workload | Built from [app/](app/) with [app/rockcraft.yaml](app/rockcraft.yaml) and attached to the charm as the `app-image` OCI resource. |

### Self-check before requesting a review

The review automation checks part of the list itself. Run the same checks
locally from the repository root:

```bash
uvx --from git+https://github.com/canonical/charmhub-listing-review self-review \
  --charm-name gopkg-k8s \
  --repository https://github.com/canonical/gopkg-charmed \
  --charm-dir app/charm \
  --ci-linting-url https://github.com/canonical/gopkg-charmed/blob/main/.github/workflows/test.yaml
```

Items the tool reports as needing manual review are checked by the reviewer
on the issue. The licence check only recognises a few licence texts by hash,
so it does not tick BSD-2-Clause automatically; point the reviewer at
`LICENSE`.
