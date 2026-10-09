# Benchmark Portability Addendum

Date: 2026-10-08.
This addendum amends `docs/specs/2026-10-08_ProductionReadiness.md`, specifically its "Benchmark Gate" section, and wins wherever the two disagree.

## Motivation

- A single committed absolute wall-clock baseline recorded on one runner is machine-picky, because it bakes that host's speed into the gate.
- The measured mac-vs-CI skew was 2.4x, so a baseline recorded on the runner fails on a developer machine and the reverse also fails.
- The gated `load:*:delta_ms` metric is signed startup noise, because the plugin file is tiny and the real load cost is sourcing the 3797-line `data.vim`.

## Revised Gate Model

- The gate now compares same-run ratios, so it is host-independent.
- The key `exec:<editor>:<payload>:<lines>:ratio` is the payload time divided by the calibration time from the same run.
- The key `load:<editor>:source_ratio` is `source_data_ms` divided by the calibration time from the same run.
- `load:*:delta_ms` is still recorded but is no longer gated.
- The `exec:<editor>:empty:1` metric is recorded but not gated, because it is sub-microsecond scheduling noise.
- An editor-version difference from the baseline emits a warning, not a failure, so a version bump without a re-record is visible.
- A missing gated metric is now a failure instead of a warning.
- The check is advisory by default and enforcing (exit 1 on violations) when `CI` is set or `--enforce` is passed.

## Portable Bench Changes

- `bench/run.sh` honors `VIM_BIN` and `NVIM_BIN` and hard-fails when either binary is missing.
- The harness uses a portable Python timer and `mktemp`.
- `bench/run.sh` accepts space-separated dimensions (`exec`, `load`, `all`).

## Baseline Recording Rule

- The committed baseline is recorded only on the `ubuntu-latest` runner through the human-triggered Bench Baseline workflow, never from a developer machine.
- `make bench-record` refuses to overwrite `bench/baseline.json` unless `BENCH_RECORD_FORCE=1` is set.

## Runner And Editor Install

- CI uses `ubuntu-latest` and installs Vim from the distribution and Neovim from the pinned prebuilt tarball, instead of `rhysd/action-setup-vim`.
- The change is required because `ubuntu-latest` moves to 26.04 (runner-images #14748), where the pinned action fails with `EXDEV` (issue #80).
- The `vim-old` leg was dropped; the Vim 8.0 floor was proven at the 2026-10-08 release.
