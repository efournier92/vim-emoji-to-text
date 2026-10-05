#!/usr/bin/env python3
"""Release-time refresh: pin the latest iamcal/emoji-data tag and regenerate.

Queries upstream tags, selects the highest semver tag, rewrites the pin
constants in tools/generate_map.py, downloads and hashes that revision,
regenerates autoload/emoji_to_text/data.vim in place, and updates the
README revision line. --dry-run only prints the selected tag.
"""

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import generate_map

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
TAGS_API = "https://api.github.com/repos/iamcal/emoji-data/tags?per_page=100"
RAW_URL = "https://raw.githubusercontent.com/iamcal/emoji-data/%s/emoji.json"
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
README_LINE = re.compile(r"^Pinned dataset: .*$", re.MULTILINE)


def semver_key(tag):
    match = SEMVER.match(tag)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def select_latest_tag(tags):
    candidates = [
        (semver_key(tag["name"]), tag) for tag in tags
    ]
    candidates = [(key, tag) for key, tag in candidates if key is not None]
    if not candidates:
        raise SystemExit("No semver tag found upstream")
    return max(candidates, key=lambda item: item[0])[1]


def fetch_tags():
    request = urllib.request.Request(TAGS_API, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return [
        {"name": tag["name"], "sha": tag["commit"]["sha"]}
        for tag in data
    ]


def download_dataset(commit):
    with urllib.request.urlopen(RAW_URL % commit, timeout=60) as response:
        raw = response.read()
    return raw, hashlib.sha256(raw).hexdigest()


def rewrite_pin(tag, commit, digest, date=None):
    date = date or datetime.date.today().isoformat()
    path = TOOLS_DIR / "generate_map.py"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'^SOURCE_TAG = ".*"$', 'SOURCE_TAG = "%s"' % tag, text, flags=re.M)
    text = re.sub(
        r'^SOURCE_COMMIT = ".*"$', 'SOURCE_COMMIT = "%s"' % commit, text, flags=re.M
    )
    text = re.sub(
        r'^SOURCE_SHA256 = ".*"$', 'SOURCE_SHA256 = "%s"' % digest, text, flags=re.M
    )
    text = re.sub(
        r'^SOURCE_DATE = ".*"$', 'SOURCE_DATE = "%s"' % date, text, flags=re.M
    )
    path.write_text(text, encoding="utf-8")


def update_readme(tag, commit):
    path = REPO_ROOT / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    line = "Pinned dataset: iamcal/emoji-data %s (%s)" % (tag, commit)
    if README_LINE.search(text):
        text = README_LINE.sub(line, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + line + "\n"
    path.write_text(text, encoding="utf-8")


def run_generator(dataset_path):
    subprocess.run(
        [
            sys.executable,
            str(TOOLS_DIR / "generate_map.py"),
            "--input",
            str(dataset_path),
            "--output",
            str(REPO_ROOT / generate_map.DEFAULT_OUTPUT),
        ],
        check=True,
        cwd=str(REPO_ROOT),
    )


def refresh(dry_run=False, today=None):
    latest = select_latest_tag(fetch_tags())
    tag, commit = latest["name"], latest["sha"]

    if dry_run:
        print("Latest upstream tag: %s (%s)" % (tag, commit))
        return 0

    if tag == generate_map.SOURCE_TAG and commit == generate_map.SOURCE_COMMIT:
        print("Pin already at %s (%s); nothing to do" % (tag, commit))
        return 0

    raw, digest = download_dataset(commit)
    rewrite_pin(tag, commit, digest, today)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
        handle.write(raw)
        dataset_path = handle.name
    try:
        run_generator(dataset_path)
    finally:
        Path(dataset_path).unlink(missing_ok=True)
    update_readme(tag, commit)
    print("Refreshed pin to %s (%s)" % (tag, commit))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the selected upstream tag without writing anything",
    )
    args = parser.parse_args(argv)
    return refresh(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
