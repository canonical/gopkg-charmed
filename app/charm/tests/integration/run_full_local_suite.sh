#!/usr/bin/env bash
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -euo pipefail

# Run the full charm integration suite locally on Linux amd64/arm64.
# This script builds artifacts, pushes the local image, and executes tox integration tests.

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This script must run in Linux."
  echo "If you are on macOS, run it inside your Multipass VM where MicroK8s and Juju are installed."
  exit 1
fi

for cmd in dpkg rockcraft charmcraft juju microk8s tox; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
done

ARCH="$(dpkg --print-architecture)"
if [[ "$ARCH" != "amd64" && "$ARCH" != "arm64" ]]; then
  echo "Unsupported architecture: $ARCH"
  echo "Supported architectures: amd64, arm64"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
APP_DIR="$REPO_ROOT/app"
CHARM_DIR="$REPO_ROOT/app/charm"
ROCK_FILE="$APP_DIR/gopkg_0.1_${ARCH}.rock"
APP_IMAGE="localhost:32000/gopkg:0.1"

echo "==> Ensuring MicroK8s is ready"
microk8s status --wait-ready >/dev/null

echo "==> Ensuring required MicroK8s add-ons"
sudo microk8s enable hostpath-storage registry ingress >/dev/null

echo "==> Ensuring Juju controller exists"
if ! juju controllers >/dev/null 2>&1; then
  echo "No Juju controller found. Bootstrapping 'dev' on microk8s..."
  juju bootstrap microk8s dev
fi

echo "==> Building rock (${ARCH})"
pushd "$APP_DIR" >/dev/null
ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
if [[ ! -f "$ROCK_FILE" ]]; then
  echo "Expected rock not found: $ROCK_FILE"
  exit 1
fi

echo "==> Pushing rock to local registry"
rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false \
  "oci-archive:$ROCK_FILE" \
  "docker://$APP_IMAGE"
popd >/dev/null

echo "==> Building charm"
pushd "$CHARM_DIR" >/dev/null
CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack

shopt -s nullglob
charm_files=(gopkg-charmed_*.charm)
shopt -u nullglob

if [[ ${#charm_files[@]} -eq 0 ]]; then
  echo "No packed charm found in $CHARM_DIR"
  exit 1
fi
CHARM_FILE="${charm_files[0]}"

echo "==> Running full Juju integration suite"
echo "Using CHARM_FILE=$CHARM_FILE"
echo "Using APP_IMAGE=$APP_IMAGE"
CHARM_FILE="$CHARM_FILE" APP_IMAGE="$APP_IMAGE" tox -e integration
popd >/dev/null

echo "==> Full local Juju integration suite completed"
