"""Benchmark gate: parser, record, and tolerance check.

    python3 test/test_bench.py
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("bench_check", ROOT / "bench" / "check.py")
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)

EXEC_LINE = "exec editor=vim heavy lines=1000 reps=1 per_run_ms=113.417"


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = bench.main(argv)
    return code, out.getvalue(), err.getvalue()


class BenchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text)
        return str(path)

    def test_parser_maps_exec_line(self):
        metrics = bench.parse_lines(EXEC_LINE)
        self.assertEqual(metrics["exec:vim:heavy:1000:per_run_ms"], 113.417)

    def test_parser_maps_load_and_gated_fields(self):
        metrics = bench.parse_lines("load editor=vim base_ms=1.0 plugin_ms=1.1 delta_ms=0.1")
        self.assertEqual(metrics["load:vim:delta_ms"], 0.1)
        self.assertTrue(bench.is_gated("load:vim:delta_ms"))
        self.assertFalse(bench.is_gated("load:vim:base_ms"))

    def test_check_passes_within_tolerance(self):
        run = self.write("run.txt", EXEC_LINE)
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:per_run_ms": 100.0}}))
        code, _, _ = run_main(["--check", "--input", run, "--baseline", baseline])
        self.assertEqual(code, 0)

    def test_check_fails_listing_key_over_tolerance(self):
        run = self.write("run.txt", "exec editor=vim heavy lines=1000 reps=1 per_run_ms=200.0")
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:per_run_ms": 100.0}}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline])
        self.assertEqual(code, 1)
        self.assertIn("exec:vim:heavy:1000:per_run_ms", err)

    def test_check_fails_when_gated_metric_missing_from_baseline(self):
        run = self.write("run.txt", EXEC_LINE)
        baseline = self.write("baseline.json", json.dumps({"tolerance": 0.5, "metrics": {}}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline])
        self.assertEqual(code, 1)
        self.assertIn("re-record the baseline", err)

    def test_check_accepts_negative_load_delta_within_tolerance(self):
        run = self.write("run.txt", "load editor=vim base_ms=8.0 plugin_ms=6.0 delta_ms=-2.0")
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"load:vim:delta_ms": -3.0}}))
        code, _, _ = run_main(["--check", "--input", run, "--baseline", baseline])
        self.assertEqual(code, 0)

    def test_check_fails_negative_load_delta_regression(self):
        run = self.write("run.txt", "load editor=vim base_ms=8.0 plugin_ms=7.5 delta_ms=-0.5")
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"load:vim:delta_ms": -3.0}}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline])
        self.assertEqual(code, 1)
        self.assertIn("load:vim:delta_ms", err)

    def test_record_writes_expected_json_shape(self):
        run = self.write("run.txt", EXEC_LINE)
        out = str(self.dir / "out.json")
        code, _, _ = run_main(["--record", "--input", run, "--output", out,
                               "--editor-versions", '{"vim": "VIM 9.2"}'])
        self.assertEqual(code, 0)
        data = json.loads(Path(out).read_text())
        self.assertEqual(set(data), {"recorded_on", "editor_versions", "tolerance", "metrics"})
        self.assertEqual(data["tolerance"], 0.5)
        self.assertEqual(data["metrics"]["exec:vim:heavy:1000:per_run_ms"], 113.417)

    def test_bench_tolerance_env_overrides_default(self):
        run = self.write("run.txt", EXEC_LINE)
        out = str(self.dir / "out.json")
        with mock.patch.dict(os.environ, {"BENCH_TOLERANCE": "0.1"}):
            code, _, _ = run_main(["--record", "--input", run, "--output", out,
                                   "--editor-versions", "{}"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(Path(out).read_text())["tolerance"], 0.1)


if __name__ == "__main__":
    unittest.main()
