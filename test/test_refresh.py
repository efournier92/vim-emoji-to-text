"""Tests for tools/refresh_map.py.

Covers Test Plan case 24: the dry run selects the highest semver tag
and writes nothing. Network calls are stubbed so the test is offline.

    python3 test/test_refresh.py
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import refresh_map as refresh  # noqa: E402


TAGS = [
    {"name": "v1.2.3", "sha": "a"},
    {"name": "v16.0.0", "sha": "b"},
    {"name": "v9.9.9", "sha": "c"},
    {"name": "v15.0.1", "sha": "d"},
    {"name": "nightly", "sha": "e"},
    {"name": "v1.0", "sha": "f"},
    {"name": "docs", "sha": "g"},
]


class RefreshTest(unittest.TestCase):
    def test_selects_highest_semver(self):
        latest = refresh.select_latest_tag(TAGS)
        self.assertEqual(latest["name"], "v16.0.0")
        self.assertEqual(latest["sha"], "b")

    def test_dry_run_prints_tag_and_writes_nothing(self):
        writes = []
        original = (refresh.fetch_tags, refresh.download_dataset,
                    refresh.rewrite_pin, refresh.update_readme)
        refresh.fetch_tags = lambda: TAGS
        refresh.download_dataset = lambda commit: writes.append("download")
        refresh.rewrite_pin = lambda *a, **k: writes.append("pin")
        refresh.update_readme = lambda *a, **k: writes.append("readme")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = refresh.main(["--dry-run"])
        finally:
            (refresh.fetch_tags, refresh.download_dataset,
             refresh.rewrite_pin, refresh.update_readme) = original
        self.assertEqual(code, 0)
        self.assertEqual(writes, [])
        self.assertIn("v16.0.0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
