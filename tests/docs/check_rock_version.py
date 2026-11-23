#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Check that the documentation spells the rock version from app/rockcraft.yaml.

`rockcraft pack` writes <name>_<version>_<arch>.rock, and the pages that build
from source copy that file and push it under an image tag that starts with the
same version. No CI job runs those commands, so a version change that misses a
page goes unnoticed until a reader copies the command. This script compares
every such reference in the Markdown and RST files with app/rockcraft.yaml and
exits non-zero on a mismatch.

Usage: python3 tests/docs/check_rock_version.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROCKCRAFT_YAML = "app/rockcraft.yaml"
# Release notes describe earlier releases, so they may name earlier versions.
SKIPPED_PREFIXES = ("docs/release-notes/",)


def rockcraft_value(text, key):
    """Return a top-level scalar from app/rockcraft.yaml, without quotes."""
    match = re.search(rf"^{key}:[ \t]*(['\"]?)([^'\"\s#]+)\1[ \t]*(#.*)?$", text, re.MULTILINE)
    if match is None:
        sys.exit(f"{ROCKCRAFT_YAML}: no top-level '{key}' key")
    return match.group(2)


def documentation_files():
    listed = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
            "*.rst",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    return sorted(
        path
        for path in listed
        if path and not path.startswith(SKIPPED_PREFIXES) and (ROOT / path).is_file()
    )


def report(path, line, message):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::error file={path},line={line}::{path}:{line}: {message}")
    else:
        print(f"{path}:{line}: {message}")


def main():
    rockcraft = (ROOT / ROCKCRAFT_YAML).read_text(encoding="utf-8")
    name = rockcraft_value(rockcraft, "name")
    version = rockcraft_value(rockcraft, "version")
    rock = re.escape(name)

    # Each pattern captures the version a reference spells. Requiring a
    # leading digit skips placeholders such as <version>, globs, shell
    # variables, and Juju endpoints such as gopkg:ingress. A tag may add a
    # suffix after a hyphen (0.1-1) to force a new pull; a file name may not.
    checks = [
        # gopkg_0.1_<architecture>.rock, gopkg_0.1_$(dpkg --print-architecture).rock
        (
            "rock file version",
            False,
            re.compile(rf"\b{rock}_(\d[^_\s]*)_(?:\$\([^)]*\)|[^\s.]*)\.rock\b"),
        ),
        # localhost:32000/gopkg:0.1, localhost:32000/gopkg:0.1-1
        ("image tag", True, re.compile(rf"(?<![\w.-]){rock}:(\d(?:[\w.-]*\w)?)")),
        # curl .../v2/gopkg/tags/list | grep -F '"0.1"'
        ("registry tag", True, re.compile(rf"/v2/{rock}/tags/list\b.*?\"(\d[^\"\s]*)\"")),
    ]

    found = 0
    mismatches = 0
    for path in documentation_files():
        text = (ROOT / path).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for kind, suffix_allowed, pattern in checks:
                for match in pattern.finditer(line):
                    found += 1
                    spelled = match.group(1)
                    if spelled == version or (
                        suffix_allowed and spelled.startswith(f"{version}-")
                    ):
                        continue
                    mismatches += 1
                    report(
                        path,
                        number,
                        f"{kind} '{spelled}' does not match "
                        f"version '{version}' in {ROCKCRAFT_YAML}",
                    )

    if found == 0:
        print(
            f"No rock file name or image tag for the '{name}' rock found in the "
            "documentation. If the rock was renamed, update the pages; if they "
            "no longer spell out the version, delete this check."
        )
        return 1
    if mismatches:
        print(
            f"{mismatches} of {found} references do not match. Update them to "
            f"version '{version}'; a tag may add a suffix, as in '{version}-1'."
        )
        return 1
    print(f"All {found} references match version '{version}' of the '{name}' rock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
