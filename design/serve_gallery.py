#!/usr/bin/env python3
"""Serve a directory for LAN preview with browser caching disabled."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=33019)
    parser.add_argument("--directory", type=Path, default=Path("results"))
    args = parser.parse_args()
    handler = partial(NoCacheHandler, directory=str(args.directory))
    HTTPServer((args.bind, args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
