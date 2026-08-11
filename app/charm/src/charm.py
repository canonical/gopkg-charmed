#!/usr/bin/env python3
# Copyright 2026 Ubuntu
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.go

logger = logging.getLogger(__name__)


class GopkgCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)


# Exclude from coverage since unit tests should not run as __main__
if __name__ == "__main__":  # pragma: no cover
    ops.main(GopkgCharm)
