#!/usr/bin/env python3
"""Compatibility entrypoint for the current public guest-media acquisition seat.

The workflow historically supplied ``--max-duration`` to the player-capture seat.
The v3 network-request harvester does not need that limit, but accepting and removing
the legacy pair keeps the workflow contract stable while it tests signed public media
requests from the same unauthenticated runner.
"""
from __future__ import annotations

import sys

from capture_public_embed_v3 import main


def drop_legacy_option(name: str) -> None:
    while name in sys.argv:
        index = sys.argv.index(name)
        del sys.argv[index]
        if index < len(sys.argv):
            del sys.argv[index]


if __name__ == "__main__":
    drop_legacy_option("--max-duration")
    main()
