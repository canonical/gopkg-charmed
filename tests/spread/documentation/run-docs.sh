#!/bin/bash
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Execute documentation pages exactly as a reader would.
#
# Each page is expanded to its shell commands with `opcli tutorial expand`,
# so the test always runs whatever the published copy-paste blocks say.
# A doc marks the points where the reader must log out and back in (for
# example, after `adduser ... snap_microk8s`) by emitting the sentinel line
# `# spread-session-break` from an invisible `.. SPREAD` block. Every
# sentinel starts a fresh login shell here, mirroring the re-login.
#
# Usage: run-docs.sh <page.rst> [<page.rst> ...]
# Pages are paths relative to the repository root, in prerequisite order.
set -euo pipefail

# On failure, print the cluster and host state so CI logs name the real
# blocker (image pull, pending PVC, disk pressure, ...) instead of only
# the timed-out command. Runs as root; never fails the run itself.
diagnose() {
  echo "===== DOCS-TEST DIAGNOSTICS (a session failed) ====="
  df -h / || true
  free -m || true
  snap list || true
  if command -v microk8s > /dev/null 2>&1; then
    microk8s kubectl get nodes -o wide || true
    microk8s kubectl describe nodes | sed -n '/Conditions:/,/Events:/p' || true
    microk8s kubectl get pods -A -o wide || true
    microk8s kubectl get pvc,pv,storageclass -A || true
    microk8s kubectl describe deployment registry -n container-registry || true
    microk8s kubectl describe pods -n container-registry || true
    microk8s kubectl get events -A --sort-by=.metadata.creationTimestamp \
      | tail -60 || true
    journalctl -u snap.microk8s.daemon-containerd --no-pager -n 50 || true
  fi
  echo "===== END DOCS-TEST DIAGNOSTICS ====="
}

script=/tmp/documentation-commands.sh
: > "${script}"
for document in "$@"; do
  opcli tutorial expand -- "${SPREAD_PATH}/${document}" >> "${script}"
  printf '\n' >> "${script}"
done

rm -f "${script}".[0-9][0-9]
awk -v prefix="${script}." '
  /^# spread-session-break$/ { n++; next }
  { print > (prefix sprintf("%02d", n)) }
' "${script}"

for session in "${script}".[0-9][0-9]; do
  if ! runuser -l ubuntu -s /bin/bash -c 'set -euxo pipefail; . "$1"' _ "${session}"; then
    diagnose
    exit 1
  fi
done
