#!/usr/bin/env python3
"""Gate a release on a CHANGELOG.md entry for a datestamp.

    python3 tools/check_changelog.py 2026-10-08
    python3 tools/check_changelog.py 2026-10-08 --print-section
"""

import argparse
import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def section(lines, date):
    """Return the body lines of the `## [date]` section, or None if absent."""
    heading = re.compile(r"^## \[" + re.escape(date) + r"\]$")
    start = next((i + 1 for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def main(argv):
    parser = argparse.ArgumentParser(description="Check for a CHANGELOG entry by date.")
    parser.add_argument("date")
    parser.add_argument("--print-section", action="store_true")
    # minimalist: --file is a test seam; the release path relies on the default.
    parser.add_argument("--file", default="CHANGELOG.md")
    args = parser.parse_args(argv)

    if not DATE_RE.match(args.date):
        print(f"invalid date: {args.date}", file=sys.stderr)
        return 2

    path = Path(args.file)
    lines = path.read_text().splitlines() if path.exists() else []
    body = section(lines, args.date)
    if body is None or not any(line.strip() for line in body):
        print(f"{args.date} changelog entry missing", file=sys.stderr)
        return 1

    if args.print_section:
        print("\n".join(body).strip("\n"))
        return 0

    print(f"{args.date} changelog entry present")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
