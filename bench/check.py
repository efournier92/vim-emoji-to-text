#!/usr/bin/env python3
"""Gate bench/run.sh metrics against a recorded baseline. Stdlib only."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TOLERANCE = 0.5
GATED = re.compile(r"^(?:exec:.+:per_run_ms|load:.+:delta_ms)$")


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


def record(input_path, output_path, recorded_on, editor_versions, tolerance):
    baseline = {
        "recorded_on": recorded_on,
        "editor_versions": editor_versions,
        "tolerance": tolerance,
        "metrics": parse_lines(Path(input_path).read_text()),
    }
    Path(output_path).write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    return baseline


def evaluate(metrics, baseline_metrics, tolerance):
    """Return (violations, warnings) for the gated metrics."""
    violations = []
    for key, value in sorted(metrics.items()):
        if not is_gated(key):
            continue
        if key not in baseline_metrics:
            violations.append("%s: missing from baseline; re-record the baseline" % key)
            continue
        baseline = baseline_metrics[key]
        # Signed metrics such as load delta_ms can be negative, where a
        # multiplicative limit has no meaning; allow the same proportional
        # headroom above the baseline in the regression direction instead.
        limit = (
            baseline * (1 + tolerance)
            if baseline >= 0
            else baseline + tolerance * abs(baseline)
        )
        if value > limit:
            violations.append("%s: baseline %s current %s (limit %s)" % (key, baseline_metrics[key], value, limit))
    warnings = [key for key in baseline_metrics if key not in metrics]
    return violations, warnings


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
    violations, warnings = evaluate(parse_lines(Path(args.input).read_text()),
                                    baseline.get("metrics", {}), tolerance)
    for key in warnings:
        print("warning: %s: in baseline but absent from run" % key, file=sys.stderr)
    if violations:
        print("bench-check failed (tolerance %s):" % tolerance, file=sys.stderr)
        for violation in violations:
            print("  " + violation, file=sys.stderr)
        return 1
    print("bench-check passed (tolerance %s)" % tolerance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
