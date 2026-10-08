"""Tests for tools/check_changelog.py.

    python3 test/test_changelog.py
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "check_changelog.py"

FULL = """\
# Changelog

## [Unreleased]

Nothing yet.

## [2026-10-08]

### Added

- Something new.

### Fixed

- Something broken.
"""


def run(content, *args):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "CHANGELOG.md"
        path.write_text(content)
        return subprocess.run(
            [sys.executable, str(TOOL), *args, "--file", str(path)],
            capture_output=True,
            text=True,
        )


class CheckChangelogTest(unittest.TestCase):
    def test_present_date_with_body_exits_zero(self):
        result = run(FULL, "2026-10-08")
        self.assertEqual(result.returncode, 0)
        self.assertIn("2026-10-08 changelog entry present", result.stdout)

    def test_missing_date_exits_one(self):
        self.assertEqual(run(FULL, "2026-01-01").returncode, 1)

    def test_empty_body_exits_one(self):
        content = "# Changelog\n\n## [2026-10-08]\n\n## [2026-10-07]\n\n- old\n"
        self.assertEqual(run(content, "2026-10-08").returncode, 1)

    def test_date_only_under_unreleased_exits_one(self):
        content = "# Changelog\n\n## [Unreleased]\n\n- work for 2026-10-08\n"
        self.assertEqual(run(content, "2026-10-08").returncode, 1)

    def test_print_section_returns_body(self):
        result = run(FULL, "2026-10-08", "--print-section")
        self.assertEqual(result.returncode, 0)
        body = "### Added\n\n- Something new.\n\n### Fixed\n\n- Something broken."
        self.assertEqual(result.stdout, body + "\n")

    def test_print_section_absent_exits_one(self):
        self.assertEqual(run(FULL, "2026-01-01", "--print-section").returncode, 1)

    def test_invalid_dates_exit_two(self):
        for bad in ("2026-10-8", "today"):
            with self.subTest(date=bad):
                self.assertEqual(run(FULL, bad).returncode, 2)


if __name__ == "__main__":
    unittest.main()
