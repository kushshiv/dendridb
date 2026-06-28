#!/usr/bin/env python3
"""Run DendriDB benchmarks and write reports."""

from __future__ import annotations

import sys

from dendridb.cli.main import app

if __name__ == "__main__":
    sys.argv = ["dendridb", "benchmark", "run", *sys.argv[1:]]
    app()
