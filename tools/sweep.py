#!/usr/bin/env python3
"""Dumps what this library answers for every ZIP code there is.

All 1,000 three-digit prefixes and all 100,000 five-digit codes, one per line.
Its twin tools/sweep.go prints the same thing from the Go side, and the two
files are compared -- which is the only way to know the two lookups agree on
inputs nobody thought to write a case for.

    python3 tools/sweep.py > /tmp/py.sweep
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ziptz  # noqa: E402  (after the path, on purpose)


def say(token):
    """One answer, error text included: what it refuses and why is as much a
    part of the port as what it resolves.

    prefix_zone and exact_zone are swept alongside zone and generic because
    they are public and because they are the two that answer "" rather than
    raising -- so a disagreement between the ports shows up as an empty column
    here and nowhere else. Location and Abbrev are left out on purpose: they
    read the system tz database, which makes them a test of the machine as much
    as of the tables, and Abbrev over 101,000 tokens costs half a minute of
    LoadLocation on the Go side for an answer Zone has already settled.
    """
    tail = f"{ziptz.prefix_zone(token[:3])}\t{ziptz.exact_zone(token)}"
    try:
        return f"{token}\t{ziptz.zone(token)}\t{ziptz.generic(token)}\t{tail}\n"
    except ziptz.ZipError as exc:
        return f"{token}\t!{exc}\t{tail}\n"


def main():
    out = sys.stdout
    out.writelines(say(f"{n:03d}") for n in range(1000))
    out.writelines(say(f"{n:05d}") for n in range(100000))


if __name__ == "__main__":
    main()
