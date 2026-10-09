#!/usr/bin/env python3
"""Gate bench/run.sh metrics against a recorded baseline. Stdlib only.

The gate compares host-independent ratios: each payload's per-run time divided
by a same-run CPU calibration, so absolute wall-clock differences between hosts
cancel out. Legacy absolute metrics are still parsed and recorded.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TOLERANCE = 0.5
CALIB_PAYLOAD = "calib"
EMPTY_PAYLOAD = "empty"
EXEC_METRIC = re.compile(r"^exec:([^:]+):([^:]+):([^:]+):per_run_ms$")
LOAD_SOURCE = re.compile(r"^load:([^:]+):source_data_ms$")
GATED = re.compile(r"^(?:exec:[^:]+:[^:]+:[^:]+:ratio|load:[^:]+:source_ratio)$")
VIM_VERSION = re.compile(r"Vi IMproved (\d+\.\d+)")
NVIM_VERSION = re.compile(r"NVIM v(\d+\.\d+\.\d+)")


def is_gated(key):
    return bool(GATED.match(key))


def parse_lines(text):
    """Map run.sh output lines to a {metric_key: value} dict."""
    metrics = {}
    for raw in text.splitlines():
        parts = raw.split()
        if not parts:
            continue
        dimension, tokens = parts[0], parts[1:]
        fields = {}
        bare = []
        for token in tokens:
            if "=" in token:
                name, _, value = token.partition("=")
                fields[name] = value
            else:
                bare.append(token)
        try:
            if dimension == "exec":
                editor = fields["editor"]
                key = "exec:%s:%s:%s:per_run_ms" % (editor, bare[0], fields["lines"])
                metrics[key] = float(fields["per_run_ms"])
            elif dimension == "load":
                editor = fields["editor"]
                for name, value in fields.items():
                    if name != "editor":
                        metrics["load:%s:%s" % (editor, name)] = float(value)
            elif dimension in ("install", "build"):
                for name, value in fields.items():
                    metrics["%s:%s" % (dimension, name)] = float(value)
        except (KeyError, IndexError, ValueError):
            # Minimalist: skip malformed lines (e.g. `exec ERROR ...`) instead of failing the gate.
            continue
    return metrics


def calibration(metrics):
    """Map editor -> calibration per_run_ms from `exec <editor> calib ...` lines."""
    calibs = {}
    for key, value in metrics.items():
        match = EXEC_METRIC.match(key)
        if match and match.group(2) == CALIB_PAYLOAD:
            calibs[match.group(1)] = value
    return calibs


def editors_needing_calibration(metrics):
    """Editors that emitted a payload or source metric, and thus need a calib."""
    editors = set()
    for key in metrics:
        match = EXEC_METRIC.match(key)
        if match:
            if match.group(2) not in (CALIB_PAYLOAD, EMPTY_PAYLOAD):
                editors.add(match.group(1))
            continue
        match = LOAD_SOURCE.match(key)
        if match:
            editors.add(match.group(1))
    return editors


def derive(metrics):
    """Return the gated ratios: payload/calib and source_data/calib per editor."""
    calibs = calibration(metrics)
    ratios = {}
    for key, value in metrics.items():
        match = EXEC_METRIC.match(key)
        if match:
            editor, payload, lines = match.groups()
            # Minimalist: empty-buffer exec is ~1us and guards no conversion, so its ratio is pure scheduling noise.
            if payload not in (CALIB_PAYLOAD, EMPTY_PAYLOAD) and editor in calibs:
                ratios["exec:%s:%s:%s:ratio" % (editor, payload, lines)] = value / calibs[editor]
            continue
        match = LOAD_SOURCE.match(key)
        if match:
            editor = match.group(1)
            if editor in calibs:
                ratios["load:%s:source_ratio" % editor] = value / calibs[editor]
    return ratios


def resolve_tolerance(cli=None, fallback=None):
    if cli is not None:
        return cli
    env = os.environ.get("BENCH_TOLERANCE")
    if env:
        return float(env)
    if fallback is not None:
        return float(fallback)
    return DEFAULT_TOLERANCE


def default_recorded_on():
    return os.environ.get("ImageOS") or os.environ.get("RUNNER_OS") or "local"


def detect_editor_versions():
    versions = {}
    for name in ("vim", "nvim"):
        try:
            out = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        first = out.splitlines()
        if first:
            versions[name] = first[0].strip()
    return versions


def normalize_version(editor, value):
    """Reduce a raw `--version` line to the editor's comparable version number."""
    pattern = NVIM_VERSION if editor == "nvim" else VIM_VERSION
    match = pattern.search(value)
    return match.group(1) if match else value.strip()


def version_drift_warnings(baseline_versions):
    """Return warning lines for editors whose recorded version differs from the current one."""
    current = detect_editor_versions()
    warnings = []
    for editor, recorded in sorted(baseline_versions.items()):
        if editor not in current:
            continue
        old = normalize_version(editor, recorded)
        new = normalize_version(editor, current[editor])
        if old != new:
            # Minimalist: drift is surfaced, never a violation, so a version bump without a re-record stays visible.
            warnings.append("warning: %s version drift: baseline %s current %s; re-record the baseline"
                            % (editor, old, new))
    return warnings


def record(input_path, output_path, recorded_on, editor_versions, tolerance):
    baseline = {
        "recorded_on": recorded_on,
        "editor_versions": editor_versions,
        "tolerance": tolerance,
        "metrics": derive(parse_lines(Path(input_path).read_text())),
    }
    Path(output_path).write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    return baseline


def evaluate(metrics, baseline_metrics, tolerance):
    """Return (violations, derived_ratios)."""
    derived = derive(metrics)
    violations = []
    if not derived:
        violations.append("no derived ratios (empty run or no calibration)")

    calibs = calibration(metrics)
    for editor in sorted(editors_needing_calibration(metrics)):
        if editor not in calibs:
            violations.append("%s: calibration missing; cannot derive ratios" % editor)

    for key, baseline in sorted(baseline_metrics.items()):
        if not is_gated(key):
            continue
        if key not in derived:
            violations.append("%s: baseline %s missing from run; re-record the baseline" % (key, baseline))
            continue
        value = derived[key]
        limit = baseline * (1 + tolerance)
        if value > limit:
            violations.append("%s: baseline %s current %s (limit %s)" % (key, baseline, value, limit))
    return violations, derived


def ci_truthy():
    return os.environ.get("CI", "").strip().lower() in ("true", "1", "yes")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--baseline")
    parser.add_argument("--tolerance", type=float)
    parser.add_argument("--recorded-on")
    parser.add_argument("--editor-versions")
    parser.add_argument("--enforce", action="store_true")
    parser.add_argument("--advisory", action="store_true")
    args = parser.parse_args(argv)
    if args.record == args.check:
        parser.error("choose exactly one of --record or --check")

    if args.record:
        if not args.output:
            parser.error("--record requires --output")
        versions = json.loads(args.editor_versions) if args.editor_versions else detect_editor_versions()
        record(args.input, args.output, args.recorded_on or default_recorded_on(),
               versions, resolve_tolerance(args.tolerance))
        return 0

    if not args.baseline:
        parser.error("--check requires --baseline")
    baseline = json.loads(Path(args.baseline).read_text())
    tolerance = resolve_tolerance(args.tolerance, baseline.get("tolerance"))
    metrics = parse_lines(Path(args.input).read_text())
    violations, derived = evaluate(metrics, baseline.get("metrics", {}), tolerance)

    recorded_versions = baseline.get("editor_versions") or {}
    if recorded_versions:
        for warning in version_drift_warnings(recorded_versions):
            print(warning)

    # An empty derived set is a hard failure: the gate has nothing to guard.
    if not derived:
        print("bench-check failed (tolerance %s):" % tolerance, file=sys.stderr)
        for violation in violations:
            print("  " + violation, file=sys.stderr)
        return 1

    if not violations:
        print("bench-check passed (tolerance %s)" % tolerance)
        return 0

    enforce = (args.enforce or ci_truthy()) and not args.advisory
    if enforce:
        print("bench-check failed (tolerance %s):" % tolerance, file=sys.stderr)
        for violation in violations:
            print("  " + violation, file=sys.stderr)
        return 1
    for violation in violations:
        print("advisory: " + violation)
    return 0


if __name__ == "__main__":
    sys.exit(main())
