#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""stand-in pdftoppm: renders one-*.pdf (the tool's single-page copies) differently from the full file"""
import os
import sys

args = sys.argv[1:]
if "one-" in " ".join(args):
    args = ["-mono"] + args
os.execv("/opt/homebrew/bin/pdftoppm", ["/opt/homebrew/bin/pdftoppm"] + args)
