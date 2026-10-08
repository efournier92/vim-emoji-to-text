"""Tests for tools/refresh_map.py.

Covers the refresh test plan: dry run selects the highest semver tag and
writes nothing; render_* helpers rewrite only their target lines; the
success path writes all four files; and a failure before the write phase
leaves the tree untouched. Network calls are stubbed so the test is
offline.

    python3 test/test_refresh.py
"""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import generate_map as gen  # noqa: E402
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

GEN_SOURCE = (
    'SOURCE_TAG = "v1.0.0"\n'
    'SOURCE_COMMIT = "oldcommit"\n'
    'SOURCE_SHA256 = "oldsha"\n'
    'SOURCE_DATE = "2020-01-01"\n'
    'GENERATOR_VERSION = "0.1.0"\n'
)

NOTICE_SOURCE = (
    "Emoji shortcode data\n"
    "--------------------\n"
    "\n"
    "    https://github.com/iamcal/emoji-data\n"
    "    Pinned revision: v1.0.0 (oldcommit)\n"
    "    Licensed under the MIT License.\n"
)

NOTICE_NO_PIN = (
    "Emoji shortcode data\n"
    "--------------------\n"
    "\n"
    "    https://github.com/iamcal/emoji-data\n"
    "    Licensed under the MIT License.\n"
)

README_SOURCE = (
    "Title\n"
    "\n"
    "Pinned dataset: iamcal/emoji-data v1.0.0 (oldcommit)\n"
    "\n"
    "More text.\n"
)

README_NO_PIN = "Title\n\nMore text.\n"

TINY_DATASET = json.dumps(
    [
        {
            "unified": "1F600",
            "short_name": "grinning",
            "short_names": ["grinning"],
            "category": "Smileys & Emotion",
            "skin_variations": {},
        }
    ]
).encode("utf-8")


class RefreshTest(unittest.TestCase):
    def test_selects_highest_semver(self):
        latest = refresh.select_latest_tag(TAGS)
        self.assertEqual(latest["name"], "v16.0.0")
        self.assertEqual(latest["sha"], "b")

    def test_render_pin_replaces_all_four_and_keeps_rest(self):
        out = refresh.render_pin(GEN_SOURCE, "v2.0.0", "newcommit", "newsha", "2026-10-08")
        self.assertIn('SOURCE_TAG = "v2.0.0"', out)
        self.assertIn('SOURCE_COMMIT = "newcommit"', out)
        self.assertIn('SOURCE_SHA256 = "newsha"', out)
        self.assertIn('SOURCE_DATE = "2026-10-08"', out)
        self.assertIn('GENERATOR_VERSION = "0.1.0"', out)
        self.assertEqual(out.count('SOURCE_'), 4)

    def test_render_notice_replaces_existing_pin(self):
        out = refresh.render_notice(NOTICE_SOURCE, "v2.0.0", "newcommit")
        self.assertIn("    Pinned revision: v2.0.0 (newcommit)", out)
        self.assertNotIn("v1.0.0", out)
        self.assertIn("    Licensed under the MIT License.", out)

    def test_render_notice_appends_when_absent(self):
        out = refresh.render_notice(NOTICE_NO_PIN, "v2.0.0", "newcommit")
        self.assertIn("    Pinned revision: v2.0.0 (newcommit)", out)
        self.assertIn("    https://github.com/iamcal/emoji-data", out)
        self.assertIn("    Licensed under the MIT License.", out)

    def test_render_readme_replaces_existing(self):
        out = refresh.render_readme(README_SOURCE, "v2.0.0", "newcommit")
        self.assertIn(
            "Pinned dataset: iamcal/emoji-data v2.0.0 (newcommit)", out
        )
        self.assertIn("More text.", out)

    def test_render_readme_appends_when_absent(self):
        out = refresh.render_readme(README_NO_PIN, "v2.0.0", "newcommit")
        self.assertIn(
            "Pinned dataset: iamcal/emoji-data v2.0.0 (newcommit)", out
        )
        self.assertIn("More text.", out)

    def _temp_repo(self, tmp):
        tools = Path(tmp) / "tools"
        tools.mkdir()
        (tools / "generate_map.py").write_text(GEN_SOURCE, encoding="utf-8")
        (Path(tmp) / "README.md").write_text(README_SOURCE, encoding="utf-8")
        (Path(tmp) / "NOTICE").write_text(NOTICE_SOURCE, encoding="utf-8")
        return Path(tmp)

    def _patched(self, root, output="data.vim"):
        saved = (refresh.TOOLS_DIR, refresh.REPO_ROOT, gen.DEFAULT_OUTPUT)
        refresh.TOOLS_DIR = root / "tools"
        refresh.REPO_ROOT = root
        gen.DEFAULT_OUTPUT = output
        return saved

    def _restore(self, saved):
        refresh.TOOLS_DIR, refresh.REPO_ROOT, gen.DEFAULT_OUTPUT = saved

    def test_success_writes_all_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._temp_repo(tmp)
            saved = self._patched(root)
            saved_net = (refresh.fetch_tags, refresh.download_dataset)
            refresh.fetch_tags = lambda: [{"name": "v99.0.0", "sha": "deadbeef"}]
            refresh.download_dataset = lambda commit: (
                TINY_DATASET,
                hashlib.sha256(TINY_DATASET).hexdigest(),
            )
            try:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = refresh.refresh(today="2026-10-08")
            finally:
                (refresh.fetch_tags, refresh.download_dataset) = saved_net
                self._restore(saved)

            self.assertEqual(code, 0)
            pin = (root / "tools" / "generate_map.py").read_text()
            self.assertIn('SOURCE_TAG = "v99.0.0"', pin)
            self.assertIn('SOURCE_COMMIT = "deadbeef"', pin)
            self.assertIn('SOURCE_DATE = "2026-10-08"', pin)

            dataset = (root / "data.vim").read_text()
            self.assertIn('" SOURCE_TAG: v99.0.0', dataset)
            self.assertIn('" SOURCE_COMMIT: deadbeef', dataset)

            readme = (root / "README.md").read_text()
            self.assertIn(
                "Pinned dataset: iamcal/emoji-data v99.0.0 (deadbeef)", readme
            )
            notice = (root / "NOTICE").read_text()
            self.assertIn("    Pinned revision: v99.0.0 (deadbeef)", notice)

    def test_failure_before_write_leaves_tree_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._temp_repo(tmp)
            saved = self._patched(root)
            paths = [
                root / "tools" / "generate_map.py",
                root / "data.vim",
                root / "README.md",
                root / "NOTICE",
            ]
            before = [(p.read_bytes() if p.exists() else None) for p in paths]
            saved_net = (refresh.fetch_tags, refresh.download_dataset)
            saved_build = gen.build_map
            refresh.fetch_tags = lambda: [{"name": "v99.0.0", "sha": "deadbeef"}]
            refresh.download_dataset = lambda commit: (
                TINY_DATASET,
                hashlib.sha256(TINY_DATASET).hexdigest(),
            )

            def boom(entries):
                raise SystemExit("collision")

            gen.build_map = boom
            try:
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stdout(io.StringIO()):
                        refresh.refresh(today="2026-10-08")
            finally:
                gen.build_map = saved_build
                (refresh.fetch_tags, refresh.download_dataset) = saved_net
                self._restore(saved)

            after = [(p.read_bytes() if p.exists() else None) for p in paths]
            self.assertEqual(before, after)

    def test_noop_when_pin_matches(self):
        calls = []
        original = refresh.fetch_tags
        refresh.fetch_tags = lambda: [
            {"name": gen.SOURCE_TAG, "sha": gen.SOURCE_COMMIT}
        ]
        refresh.download_dataset = lambda commit: calls.append("download")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = refresh.refresh()
        finally:
            refresh.fetch_tags = original
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])
        self.assertIn("nothing to do", out.getvalue())

    def test_dry_run_prints_tag_and_writes_nothing(self):
        writes = []
        original = (refresh.fetch_tags, refresh.download_dataset)
        refresh.fetch_tags = lambda: TAGS
        refresh.download_dataset = lambda commit: writes.append("download")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = refresh.main(["--dry-run"])
        finally:
            (refresh.fetch_tags, refresh.download_dataset) = original
        self.assertEqual(code, 0)
        self.assertEqual(writes, [])
        self.assertIn("v16.0.0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
