#!/usr/bin/env python3
"""Compatibility entrypoint for the current public guest-media acquisition seat.

The earlier referrer-aware player seat proved that GitHub runners still receive a
bot-confirmation overlay, but its diagnostics also revealed signed public
``googlevideo.com/videoplayback`` requests. Delegate to v3, which immediately tests
those observed bytes from the same guest runner before the signature expires.
"""
from capture_public_embed_v3 import main


if __name__ == "__main__":
    main()
