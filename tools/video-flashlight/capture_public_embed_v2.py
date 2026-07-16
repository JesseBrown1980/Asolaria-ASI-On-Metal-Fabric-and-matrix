#!/usr/bin/env python3
"""Compatibility entrypoint for the current public guest-media acquisition seat.

The v4 seat waits for and stimulates the public player, records signed media requests,
and fetches those public bytes through the same unauthenticated browser context before
closing it. The workflow's historical CLI remains accepted by v4 directly.
"""
from capture_public_embed_v4 import main


if __name__ == "__main__":
    main()
