#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""stand-in pdftoppm: every page number after -f or -l is incremented by one"""
import os
import sys

args = sys.argv[1:]
for i in range(len(args) - 1):
    if args[i] in ("-f", "-l"):
        args[i + 1] = str(int(args[i + 1]) + 1)
os.execv("/opt/homebrew/bin/pdftoppm", ["/opt/homebrew/bin/pdftoppm"] + args)
