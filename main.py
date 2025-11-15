#!/usr/bin/env python3
"""Launcher for the refactored bomberman package.

This small launcher ensures the `src` directory is on sys.path so running
`python3 main.py` still works from the project root.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from bomberman.main import main

if __name__ == "__main__":
    main()