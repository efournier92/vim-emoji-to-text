#!/usr/bin/env python3
"""Release-time refresh: pin the latest iamcal/emoji-data tag and regenerate.

Queries upstream tags, selects the highest semver tag, rewrites the pin
constants in tools/generate_map.py, downloads and hashes that revision,
regenerates autoload/emoji_to_text/data.vim in place, and updates the
README revision line and NOTICE. Every file is computed in memory before
any write, and each write goes through a temp file plus os.replace, so a
failure before the write phase leaves the tree untouched. --dry-run only
prints the selected tag.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import generate_map

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
TAGS_API = "https://api.github.com/repos/iamcal/emoji-data/tags?per_page=100"
RAW_URL = "https://raw.githubusercontent.com/iamcal/emoji-data/%s/emoji.json"
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
README_LINE = re.compile(r"^Pinned dataset: .*$", re.MULTILINE)
NOTICE_PIN = re.compile(r"^    Pinned revision: .*$", re.MULTILINE)
NOTICE_ANCHOR = re.compile(
    r"^(?:    https://github\.com/iamcal/emoji-data|Emoji Sources)\s*$",
    re.MULTILINE,
)


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


def render_pin(source_text, tag, commit, digest, date):
    """Return generate_map.py text with the four SOURCE_* lines repinned."""
    text = re.sub(r'^SOURCE_TAG = ".*"$', 'SOURCE_TAG = "%s"' % tag, source_text, flags=re.M)
    text = re.sub(
        r'^SOURCE_COMMIT = ".*"$', 'SOURCE_COMMIT = "%s"' % commit, text, flags=re.M
    )
    text = re.sub(
        r'^SOURCE_SHA256 = ".*"$', 'SOURCE_SHA256 = "%s"' % digest, text, flags=re.M
    )
    return re.sub(
        r'^SOURCE_DATE = ".*"$', 'SOURCE_DATE = "%s"' % date, text, flags=re.M
    )


def render_notice(source_text, tag, commit):
    """Return NOTICE text with the pinned revision updated or added."""
    line = "    Pinned revision: %s (%s)" % (tag, commit)
    if NOTICE_PIN.search(source_text):
        return NOTICE_PIN.sub(line, source_text, count=1)
    anchor = NOTICE_ANCHOR.search(source_text)
    if anchor:
        # minimalist: insert after the block heading/URL; rest stays byte-identical.
        return source_text[:anchor.end()] + "\n" + line + source_text[anchor.end():]
    return source_text.rstrip() + "\n\n" + line + "\n"


def render_readme(source_text, tag, commit):
    """Return README text with the pinned dataset line updated or added."""
    line = "Pinned dataset: iamcal/emoji-data %s (%s)" % (tag, commit)
    if README_LINE.search(source_text):
        return README_LINE.sub(line, source_text, count=1)
    return source_text.rstrip() + "\n\n" + line + "\n"


def write_atomic(path, text):
    """Write text via a sibling temp file and os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def rewrite_pin(tag, commit, digest, date=None):
    date = date or datetime.date.today().isoformat()
    path = TOOLS_DIR / "generate_map.py"
    text = path.read_text(encoding="utf-8")
    write_atomic(path, render_pin(text, tag, commit, digest, date))


def refresh(dry_run=False, today=None):
    date = today or datetime.date.today().isoformat()
    latest = select_latest_tag(fetch_tags())
    tag, commit = latest["name"], latest["sha"]

    if dry_run:
        print("Latest upstream tag: %s (%s)" % (tag, commit))
        return 0

    if tag == generate_map.SOURCE_TAG and commit == generate_map.SOURCE_COMMIT:
        print("Pin already at %s (%s); nothing to do" % (tag, commit))
        return 0

    raw, digest = download_dataset(commit)

    # Compute every output before touching the tree (compute-first, write-last).
    pin_path = TOOLS_DIR / "generate_map.py"
    pin_text = render_pin(
        pin_path.read_text(encoding="utf-8"), tag, commit, digest, date
    )
    readme_path = REPO_ROOT / "README.md"
    readme_text = (
        render_readme(readme_path.read_text(encoding="utf-8"), tag, commit)
        if readme_path.exists()
        else None
    )
    notice_path = REPO_ROOT / "NOTICE"
    notice_text = (
        render_notice(notice_path.read_text(encoding="utf-8"), tag, commit)
        if notice_path.exists()
        else None
    )
    # The header must describe the NEW pin, so build meta from it rather than
    # generate_map.default_meta(), which reads the stale module globals.
    meta = {
        "source_url": RAW_URL % commit,
        "source_tag": tag,
        "source_commit": commit,
        "sha256": digest,
        "refreshed": date,
        "generator": generate_map.GENERATOR_VERSION,
    }
    entries = json.loads(raw.decode("utf-8"))
    dataset_text = generate_map.render_vim(generate_map.build_map(entries), meta)

    write_atomic(pin_path, pin_text)
    write_atomic(REPO_ROOT / generate_map.DEFAULT_OUTPUT, dataset_text)
    if readme_text is not None:
        write_atomic(readme_path, readme_text)
    if notice_text is not None:
        write_atomic(notice_path, notice_text)

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
