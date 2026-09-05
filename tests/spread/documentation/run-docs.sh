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
  runuser -l ubuntu -s /bin/bash -c 'set -euxo pipefail; . "$1"' _ "${session}"
done
