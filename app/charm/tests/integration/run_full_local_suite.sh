#!/usr/bin/env bash
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -euo pipefail

# Run the full charm integration suite locally on Linux amd64/arm64, the way
# CI runs it: on Canonical Kubernetes, prepared by concierge from the same
# file. The script installs tools with sudo and cannot share a machine with
# MicroK8s, so run it in a fresh Ubuntu 24.04 VM.
#
# CONCIERGE selects the concierge file, as in spread.yaml: concierge-lxd.yaml
# (default) for Juju 3, concierge-juju4.yaml for Juju 4. Use one VM for each.

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This script must run in Linux."
  echo "If you are on macOS, run it inside a fresh Multipass VM."
  exit 1
fi

ARCH="$(dpkg --print-architecture)"
if [[ "$ARCH" != "amd64" && "$ARCH" != "arm64" ]]; then
  echo "Unsupported architecture: $ARCH"
  echo "Supported architectures: amd64, arm64"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
APP_DIR="$REPO_ROOT/app"
CHARM_DIR="$REPO_ROOT/app/charm"
CONCIERGE="${CONCIERGE:-concierge-lxd.yaml}"
CONCIERGE_FILE="$REPO_ROOT/$CONCIERGE"
ROCK_FILE="$APP_DIR/gopkg_0.1_${ARCH}.rock"
CHARM_FILE="$CHARM_DIR/gopkg-k8s_${ARCH}.charm"
# A new tag on every run, as charm-ci's opcli does: Kubernetes reuses a cached
# image whose tag has not changed, so a fixed tag would test an earlier build.
APP_IMAGE="localhost:32000/gopkg:${ARCH}-$(date +%Y%m%d-%H%M%S)"
TOX_WORK_DIR="${TOX_WORK_DIR:-$HOME/.cache/gopkg-charm-tox}"

if [[ ! -d "$REPO_ROOT/.git" || ! -f "$APP_DIR/rockcraft.yaml" || ! -f "$CHARM_DIR/charmcraft.yaml" ]]; then
  echo "Repository setup is incomplete. Mount or clone gopkg-charmed and run this script from that checkout."
  exit 1
fi

if [[ ! -f "$CONCIERGE_FILE" ]]; then
  echo "Concierge file not found: $CONCIERGE_FILE"
  echo "Set CONCIERGE to concierge-lxd.yaml or concierge-juju4.yaml."
  exit 1
fi

if snap list microk8s >/dev/null 2>&1; then
  echo "MicroK8s is installed. Canonical Kubernetes, which this script installs, cannot run next to it."
  echo "Run the script in a fresh VM: see docs/contribute/run-full-juju-integration-suite-locally.rst."
  exit 1
fi

# The Juju channel the concierge file asks for, such as 3/stable or 4.0/stable.
JUJU_CHANNEL="$(awk '/^juju:/ { in_juju = 1; next } /^[^ #]/ { in_juju = 0 }
  in_juju && $1 == "channel:" { print $2; exit }' "$CONCIERGE_FILE")"

echo "==> Preparing the machine with $CONCIERGE"
if juju show-controller concierge-k8s >/dev/null 2>&1; then
  # concierge would refresh the Juju snap to the requested channel but keep the
  # existing controller, so a run for the other Juju version would mix both.
  JUJU_VERSION="$(juju version)"
  JUJU_VERSION="${JUJU_VERSION%%-*}"
  if [[ "${JUJU_VERSION%%.*}" != "${JUJU_CHANNEL%%[./]*}" ]]; then
    echo "This machine runs Juju $JUJU_VERSION, but $CONCIERGE asks for Juju $JUJU_CHANNEL."
    echo "Run the suite for each Juju version in its own fresh VM."
    exit 1
  fi
  echo "Controller concierge-k8s exists (Juju $JUJU_VERSION); skipping preparation."
else
  if ! command -v concierge >/dev/null 2>&1; then
    sudo snap install concierge --classic
  fi
  sudo concierge prepare -c "$CONCIERGE_FILE"
fi

echo "==> Ensuring Rockcraft and tox"
if ! command -v rockcraft >/dev/null 2>&1; then
  sudo snap install rockcraft --classic
fi
if ! command -v tox >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install --yes tox
fi

echo "==> Ensuring the local image registry"
kubectl apply -f "$REPO_ROOT/app/charm/tests/integration/local-registry.yaml"
kubectl rollout status deployment/registry \
  -n container-registry --timeout=5m
curl --fail --silent --show-error --retry 30 --retry-delay 2 \
  --retry-all-errors http://localhost:32000/v2/ >/dev/null

echo "==> Building rock (${ARCH})"
pushd "$APP_DIR" >/dev/null
ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
if [[ ! -f "$ROCK_FILE" ]]; then
  echo "Expected rock not found: $ROCK_FILE"
  exit 1
fi

echo "==> Pushing rock to the local registry"
rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false \
  --dest-no-creds \
  "oci-archive:$ROCK_FILE" \
  "docker://$APP_IMAGE"
popd >/dev/null

echo "==> Building charm"
pushd "$CHARM_DIR" >/dev/null
CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
if [[ ! -f "$CHARM_FILE" ]]; then
  echo "Expected charm not found: $CHARM_FILE"
  exit 1
fi

echo "==> Running full Juju integration suite"
echo "Using CHARM_FILE=$CHARM_FILE"
echo "Using APP_IMAGE=$APP_IMAGE"
# Canonical Kubernetes's Cilium ingress is not the cluster's default class;
# CI sets the same value through spread.yaml.
CHARM_FILE="$CHARM_FILE" APP_IMAGE="$APP_IMAGE" INGRESS_CLASS=cilium \
  tox --workdir "$TOX_WORK_DIR" -e integration
popd >/dev/null

echo "==> Full local Juju integration suite completed"
