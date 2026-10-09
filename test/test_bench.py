"""Benchmark gate: parser, ratio derivation, record, and tolerance check.

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

CALIB_LINE = "exec editor=vim calib lines=20000 reps=10 per_run_ms=10.0"
EXEC_LINE = "exec editor=vim heavy lines=1000 reps=3 per_run_ms=300.0"
SOURCE_LINE = "load editor=vim source_data_ms=50.0"


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = bench.main(argv)
    return code, out.getvalue(), err.getvalue()


class BenchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        # Ambient CI would flip advisory checks to enforcement; isolate it.
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("CI", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text)
        return str(path)

    def test_parser_maps_exec_and_source_lines(self):
        metrics = bench.parse_lines(EXEC_LINE + "\n" + SOURCE_LINE)
        self.assertEqual(metrics["exec:vim:heavy:1000:per_run_ms"], 300.0)
        self.assertEqual(metrics["load:vim:source_data_ms"], 50.0)

    def test_derive_builds_exec_and_source_ratios(self):
        metrics = bench.parse_lines("\n".join([CALIB_LINE, EXEC_LINE, SOURCE_LINE]))
        ratios = bench.derive(metrics)
        self.assertEqual(ratios["exec:vim:heavy:1000:ratio"], 30.0)
        self.assertEqual(ratios["load:vim:source_ratio"], 5.0)
        self.assertTrue(bench.is_gated("exec:vim:heavy:1000:ratio"))
        self.assertTrue(bench.is_gated("load:vim:source_ratio"))
        self.assertFalse(bench.is_gated("load:vim:delta_ms"))

    def test_derive_skips_empty_payload_ratio(self):
        run = "\n".join([CALIB_LINE, "exec editor=vim empty lines=1 reps=100 per_run_ms=0.01"])
        ratios = bench.derive(bench.parse_lines(run))
        self.assertFalse(any("empty" in key for key in ratios))

    def test_check_passes_with_empty_payload_enforced(self):
        run = self.write("run.txt", "\n".join([
            CALIB_LINE, EXEC_LINE,
            "exec editor=vim empty lines=1 reps=100 per_run_ms=0.01",
        ]))
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:ratio": 31.0}}))
        code, _, _ = run_main(["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 0)

    def test_version_drift_warns_but_still_passes(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        baseline = self.write("baseline.json", json.dumps({
            "tolerance": 0.5,
            "editor_versions": {"vim": "9.0", "nvim": "0.11.0"},
            "metrics": {"exec:vim:heavy:1000:ratio": 31.0},
        }))
        detected = {
            "vim": "VIM - Vi IMproved 9.2 (2026 Feb 14, compiled Oct  8 2026 19:38:07)",
            "nvim": "NVIM v0.12.5",
        }
        with mock.patch.object(bench, "detect_editor_versions", return_value=detected):
            code, out, err = run_main(
                ["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 0)
        self.assertIn("version drift", out + err)

    def test_check_passes_within_tolerance_enforced(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:ratio": 31.0}}))
        code, _, _ = run_main(["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 0)

    def test_check_fails_over_tolerance_enforced_naming_key(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:ratio": 10.0}}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 1)
        self.assertIn("exec:vim:heavy:1000:ratio", err)
        self.assertIn("limit", err)

    def test_check_fails_when_gated_key_missing_from_run(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {
                "exec:vim:heavy:1000:ratio": 30.0,
                "exec:vim:ascii:200:ratio": 1.0,
            }}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 1)
        self.assertIn("exec:vim:ascii:200:ratio", err)

    def test_check_hard_fails_without_calibration_enforced(self):
        run = self.write("run.txt", EXEC_LINE)
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:ratio": 30.0}}))
        code, _, err = run_main(["--check", "--input", run, "--baseline", baseline, "--enforce"])
        self.assertEqual(code, 1)
        self.assertIn("no derived ratios", err)

    def test_advisory_returns_zero_despite_violations(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        baseline = self.write("baseline.json", json.dumps(
            {"tolerance": 0.5, "metrics": {"exec:vim:heavy:1000:ratio": 10.0}}))
        code, out, _ = run_main(["--check", "--input", run, "--baseline", baseline,
                                 "--enforce", "--advisory"])
        self.assertEqual(code, 0)
        self.assertIn("advisory:", out)
        self.assertIn("exec:vim:heavy:1000:ratio", out)

    def test_record_writes_derived_ratio_shape(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE, SOURCE_LINE]))
        out = str(self.dir / "out.json")
        code, _, _ = run_main(["--record", "--input", run, "--output", out,
                               "--editor-versions", '{"vim": "VIM 9.2"}'])
        self.assertEqual(code, 0)
        data = json.loads(Path(out).read_text())
        self.assertEqual(set(data), {"recorded_on", "editor_versions", "tolerance", "metrics"})
        self.assertEqual(data["tolerance"], 0.5)
        self.assertEqual(data["metrics"]["exec:vim:heavy:1000:ratio"], 30.0)
        self.assertEqual(data["metrics"]["load:vim:source_ratio"], 5.0)
        self.assertTrue(all(k.endswith("ratio") for k in data["metrics"]))

    def test_bench_tolerance_env_overrides_default(self):
        run = self.write("run.txt", "\n".join([CALIB_LINE, EXEC_LINE]))
        out = str(self.dir / "out.json")
        with mock.patch.dict(os.environ, {"BENCH_TOLERANCE": "0.1"}):
            code, _, _ = run_main(["--record", "--input", run, "--output", out,
                                   "--editor-versions", "{}"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(Path(out).read_text())["tolerance"], 0.1)


if __name__ == "__main__":
    unittest.main()
