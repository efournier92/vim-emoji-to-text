# EmojiToText: Production Readiness And Datestamp Release

> **Amended.** `docs/specs/2026-10-08_BenchmarkPortability.md` supersedes the operational parts of this spec: the gate compares same-run conversion ratios and records but does not gate the load metrics, CI uses `ubuntu-latest` and installs Vim from the distribution and Neovim from the pinned tarball, and the `vim-old` leg was dropped. Every `ubuntu-24.04`, `v9.2.1167`, `vim-old`, and gated `load:*` statement below is historical; where the two disagree, the addendum wins.

This spec closes the gaps found in the 2026-10-08 readiness pass and defines the datestamp release process.
It builds on `docs/specs/2026-10-05_EmojiToText.md`, which is historical and is not edited by this work.
Where the two disagree, this spec wins.
The work lands on `main` (a short-lived branch is fine), and the final step cuts the first release.

## Context And Motivation

- A readiness pass on 2026-10-08 ran every local gate green: `make generate-check`, `make test` (28 themis cases under Vim 9.2 and Neovim 0.12.5), `test/test_generate.py`, `test/test_encoding.py`, and `test/test_refresh.py`.
- CI on `main` is green, the repo is public with MIT detected, and the README install line matches the real remote `efournier92/vim-emoji-to-text`.
- The plugin is installable from `main`, but no release has ever been cut: `git tag -l` is empty and origin has no tags.
- The pass found five must-fix or hardening items: `NOTICE` drifts from the pin because refresh never updates it, the claimed Vim 8.0 floor is untested, `refresh_map.py` is not atomic on failure, the engine throws `E21` on a `nomodifiable` buffer, and the weekly `refresh-upstream.yml` gives no signal while contradicting the original spec.
- The pass also found missing production scaffolding: no changelog, no performance gate, no documented release process, no CI badge or requirements block, and a POSIX-only `&`/`wait` recipe in the Makefile.
- The user's release policy is datestamp versions in `YYYY-MM-DD` form, cut only by a human, with same-day re-releases overwriting the prior one.
- Nothing in this repo should happen on a timer or on an ordinary push; content stays stale until a human cuts the next version.

## Glossary

Definitions the requirements depend on are inlined here; the project glossary at `docs/GLOSSARY.md` holds the same terms for reuse.

**Pin**

The upstream dataset constants in `tools/generate_map.py` (`SOURCE_TAG`, `SOURCE_COMMIT`, `SOURCE_SHA256`, `SOURCE_DATE`). _Avoid_: lock, version.

**Dataset**

The generated `autoload/emoji_to_text/data.vim`. _Avoid_: map file (in prose that also means the dictionary).

**Refresh**

The release-time action that resolves the latest upstream tag, rewrites the pin, regenerates the dataset, and updates `README.md` and `NOTICE`. _Avoid_: sync, bump.

**Cut A Release**

The human-triggered `workflow_dispatch` run that refreshes, tests, enforces the changelog, commits, moves the datestamp tag, and creates or updates the GitHub Release. _Avoid_: publish, deploy.

**Datestamp Version**

A bare UTC date, `YYYY-MM-DD`, used as the git tag and the GitHub Release name. _Avoid_: semver tag.

**Gated Metric**

A benchmark metric that `make bench-check` compares against the baseline. _Avoid_: watched metric.

## Current State

- `Makefile:23-32` runs `test-vim` and `test-nvim` concurrently with a POSIX `&`/`wait` recipe; `test-vim` uses `THEMIS_VIM=vim`, `test-nvim` uses `THEMIS_VIM=nvim`.
- `Makefile:37-46` defines `release`; it runs `refresh_map.py`, `make test`, `make generate-check`, then `git add tools/generate_map.py autoload/emoji_to_text/data.vim README.md` and commits only when staged changes exist.
- `tools/refresh_map.py:64-79` rewrites the pin constants in `tools/generate_map.py`; `:81-91` updates only `README.md`; `:94-106` shells out to `generate_map.py` through a temporary JSON file; `:109-132` rewrites the pin at line 122 before running the generator at line 127, so a generator failure leaves a half-updated tree.
- `NOTICE:10` hardcodes `Pinned revision: v16.0.0 (2771d0b1b3af25c069086e68e38f901c3dda8bdf)`; nothing updates it.
- `autoload/emoji_to_text.vim:73-103` declines cleanly when `&encoding` is not UTF-8 (lines 75-78) but has no `&modifiable` guard; a `nomodifiable` buffer fails with `E21: Cannot make changes, 'modifiable' is off` (reproduced on 2026-10-08).
- `.github/workflows/release.yml:3-5` triggers on `push` to `v*` tags; `:6-10` takes a free-form `tag` input; `:20-46` is a `pin-guard` job with a `pin-held` bypass at line 41; `:48-93` is the release job that pushes a commit and a tag but creates no GitHub Release.
- `.github/workflows/refresh-upstream.yml:4-5` schedules a weekly cron and, at `:16-27`, runs offline tests and a dry-run that prints the selected tag without failing.
- `.github/workflows/test.yml:23-30` runs a two-entry matrix (`vim`, `nvim`) pinned to `v9.2.1167` and `v0.12.5`; the claimed Vim 8.0 floor is never executed.
- `bench/run.sh:55-66` supports `exec`, `load`, `install`, `build`, and `all`, and writes one `dimension key=value` line per metric to `$BENCH_OUT`; there is no committed baseline and no gate.
- `README.md:1-13` has no CI badge and no requirements section; `README.md:55-57` lists only `make generate-check`, `make test`, and `make refresh-check`.
- `docs/specs/2026-10-05_EmojiToText.md:165` states "there is no scheduled job"; `:173` documents the `pin-held` marker; `:302` schedules cutting `v0.1.0`. This spec supersedes all three.
- There is no `CHANGELOG.md`, no `docs/RELEASING.md`, no `bench/baseline.json`, and no `docs/GLOSSARY.md` before this spec.
- `.gitignore:1-9` ignores `vendor/`, `.themis/`, `tools/.cache/`, `doc/tags`, `__pycache__/`, `*.pyc`, `*.tmp`, and `.DS_Store`.

## Goals

- Fix every must and hardening item from the readiness pass without weakening the green suite.
- Make the shipped `NOTICE`, `README.md`, and dataset header always agree on the pin, including after a refresh.
- Make a failed refresh write nothing.
- Make the engine decline cleanly on a `nomodifiable` buffer.
- Prove the documented Vim floor with a CI leg, keeping "Vim 8.0+" only if the leg proves it.
- Add a changelog that a tag-time check forces before any release.
- Add a performance gate with a committed baseline and a tolerance.
- Make the Makefile `test` target portable by removing `&`/`wait`.
- Add a README CI badge and requirements block.
- Define one human-triggered datestamp release process, backed by `workflow_dispatch`, that refreshes to the latest upstream pin, tests, commits, moves the tag, and creates or updates a GitHub Release.
- Remove all scheduled and push-triggered release or refresh behavior.

## User Stories

1. As a maintainer, I want `NOTICE` to carry the current pin after a refresh, so that attribution and the dataset header never disagree.
2. As a maintainer, I want a failed refresh to leave every file untouched, so that a bad upstream payload cannot corrupt the repo.
3. As a writer, I want `:EmojiToText` on a read-only buffer to decline with a message, so that I do not see a raw `E21`.
4. As a maintainer, I want the changelog to have an entry for the release date, so that every release is described.
5. As a maintainer, I want the release to stop when the changelog entry is missing, so that I cannot tag an undocumented release.
6. As a maintainer, I want a committed benchmark baseline, so that a performance regression is caught.
7. As a maintainer, I want `make bench-check` to fail when a gated metric regresses past the tolerance, so that the gate is honest.
8. As a maintainer, I want the baseline to record the runner image and editor versions, so that I can judge flakiness.
9. As a contributor, I want a POSIX-safe `make test`, so that the two editor suites run without an inline `&`/`wait` recipe.
10. As a contributor, I want `make -j2 test` to run both suites in parallel, so that local iteration stays fast.
11. As a maintainer, I want a CI leg on the oldest feasible Vim 8.0.x, so that the stated floor is proven.
12. As a reader, I want the README to state requirements and link the CI status, so that I know what I am installing.
13. As a reader, I want the README to point to the release process, so that I can reproduce a release.
14. As a maintainer, I want one `workflow_dispatch` release entry point, so that a release happens only when I say so.
15. As a maintainer, I want the release to refresh to the latest upstream `iamcal/emoji-data` tag, so that a release never ships a stale dataset.
16. As a maintainer, I want the release to fail when upstream is unreachable, so that I never cut from an unpinned revision.
17. As a maintainer, I want a release to be a single commit on the default branch plus a datestamp tag, so that history stays linear.
18. As a maintainer, I want a second release on the same day to move the datestamp tag to the new commit and update the existing GitHub Release, so that the day has one canonical cut.
19. As a maintainer, I want the GitHub Release to carry the changelog section as notes and the automatic source archives, so that there is a shareable artifact.
20. As a maintainer, I want no cron and no push-triggered release or refresh, so that the repo stays still until I act.
21. As an implementer, I want the release steps to have a documented manual fallback, so that a broken runner does not block a critical release.
22. As a maintainer, I want `make release DATE=...` to be the reusable body the workflow calls, so that local and CI paths share one implementation.
23. As a maintainer, I want the generated dataset and the pin to change in the same release commit, so that `make generate-check` stays green.
24. As a user, I want the same plugin behavior after this round, so that the hardening does not change conversion output.

## Non-Goals

- No semver or `v`-prefixed tags; datestamp versions only.
- No scheduled workflows, no push-triggered release, and no automatic refresh.
- No `CONTRIBUTING.md` in this round; `docs/RELEASING.md` carries the process.
- No change to the conversion algorithm, the map contents, or the command surface.
- No new runtime dependencies; the plugin still loads from `:set rtp+=` alone.
- No editing of `docs/specs/2026-10-05_EmojiToText.md`; it is historical.
- No GitHub Actions marketplace or third-party release action; the workflow uses `gh` and git directly.
- No signing, provenance, or SBOM work in this round.

## Prerequisites

- Vim 8.0 or newer, and Neovim (floor recorded from the CI leg), each with `+eval` and `+multi_byte`.
- Python 3.8 or newer for the generator, the changelog checker, and the bench gate.
- `vim-themis` v1.7.0 for the behavior suite (development only).
- `gh` CLI available in the release workflow (preinstalled on `ubuntu-24.04`).
- A POSIX shell for local `make` targets.
- Network access at release time to resolve the latest `iamcal/emoji-data` tag and download `emoji.json`.

## Design Principles

- Human-in-the-loop: a release runs only from `workflow_dispatch`.
- One dataset artifact, refreshed only when a release is cut.
- Compute first, write last: a failed refresh changes nothing on disk.
- Fail the release, never the user.
- Same-day releases are idempotent: move the tag, update the release.
- Keep the runtime plugin pure Vimscript and dependency-free.

## Backend Requirements

### Engine Modifiable Guard

- In `autoload/emoji_to_text.vim`, immediately after the encoding guard at lines 75-78 and before the map load at line 79, add a modifiable guard.
- The guard returns early when `!&modifiable`, emitting the message `EmojiToText: buffer is not modifiable; buffer left unchanged`.
- Use `echomsg` (not `echoerr`) so the command does not raise, matching the encoding-guard style.
- The buffer, cursor, search register, and undo state must be unchanged on the early return.
- No other engine behavior changes; the documented conversion output is identical.

### Refresh Atomicity And NOTICE

Refactor `tools/refresh_map.py` so every write happens only after all content is computed.

- Add a pure function `render_pin(source_text, tag, commit, digest, date)` returning the new `tools/generate_map.py` text, replacing the four `SOURCE_*` lines; `rewrite_pin` at lines 64-79 becomes a thin wrapper that reads the file, calls `render_pin`, and writes.
- Add a pure function `render_notice(source_text, tag, commit)` returning the new `NOTICE` text: replace the `^    Pinned revision: .*$` line with `    Pinned revision: <tag> (<commit>)`, or append that line under the `Emoji Sources` block when absent.
- Add a pure function `render_readme(source_text, tag, commit)` returning the new `README.md` text, preserving the existing `README_LINE` behavior at lines 28 and 81-91.
- Replace the subprocess call in `run_generator` (lines 94-106) with an in-process `generate_map.build_map` and `generate_map.render_vim` call on the downloaded entries; remove the `subprocess` and `tempfile` imports at lines 15 and 17 when no longer used.
- Rework `refresh(dry_run=False, today=None)` at lines 109-132 to: resolve the latest tag; when the tag and commit equal the current pin, print the no-op message and return 0; otherwise download and hash the dataset, compute the new pin text, README text, NOTICE text, and dataset text in memory, and only then write all four files with a temp-file-plus-`os.replace` per file.
- On any exception before the write phase, no file is modified.
- Extend `Makefile:41` to stage `NOTICE` alongside the other release files.
- Keep `--dry-run` behavior: print `Latest upstream tag: <tag> (<commit>)` and write nothing.

### Changelog And Tag-Time Check

- Add `CHANGELOG.md` at the repo root in Keep a Changelog form, with a top `# Changelog` title, a one-paragraph intro naming datestamp versions, a `## [Unreleased]` section, and one `## [YYYY-MM-DD]` section per release.
- A datestamp section uses `### Added`, `### Changed`, and `### Fixed` subheadings as needed, each with at least one bullet.
- Same-day re-release edits the existing datestamp section in place rather than adding a second heading for the same date.
- Add `tools/check_changelog.py` (stdlib only) with this contract:
  - `check_changelog.py DATE` exits 0 and prints `<DATE> changelog entry present` when a `^## \[<DATE>\]$` heading exists with at least one non-blank body line before the next `^## ` heading.
  - It exits 1 with a message on stderr when the date is absent, the body is empty, or the date only appears under `## [Unreleased]`.
  - `check_changelog.py DATE --print-section` prints the section body (bullets only, no heading) to stdout for use as release notes; it exits 1 when the entry is missing.
  - The date is validated against `^\d{4}-\d{2}-\d{2}$`; an invalid date exits 2.
- The release path runs the check before any tag work.

### Benchmark Gate

Amended by `docs/specs/2026-10-08_BenchmarkPortability.md`: the gate is ratio-based and the load metrics are recorded but not gated.

- Add `bench/check.py` (stdlib only) that parses `bench/run.sh` output lines of the form `<dimension> editor=<editor> ... key=value ...`.
- A metric key is `exec:<editor>:<payload>:<lines>:per_run_ms` for `exec` dimensions and `load:<editor>:<field>` for `load` dimensions.
- Gated metrics are all `exec:*:per_run_ms` values and the `load:*:delta_ms` value; `install:*` and `build:*` metrics are recorded but never gated.
- `bench/check.py --record --input FILE --output bench/baseline.json` writes a baseline with `recorded_on` (the runner image, default `local`), `editor_versions`, `tolerance` (default 0.5), and a `metrics` object of `key -> value`.
- `bench/check.py --check --input FILE --baseline bench/baseline.json` exits 0 when every gated metric is present and at most `baseline * (1 + tolerance)`; it exits 1 listing each violating key with its baseline and current value.
- A gated metric missing from the baseline fails the check with a message to re-record; a baseline key absent from the run is a warning, not a failure.
- Tolerance is overridable with `--tolerance` or `BENCH_TOLERANCE`; the default is 0.5.
- Add `bench/baseline.json` recorded on `ubuntu-24.04` with Vim `v9.2.1167` and Neovim `v0.12.5`; add it to the repo and never regenerate it implicitly.
- The existing `bench/run.sh` output format is unchanged.

### Makefile Targets

- Change `test` at `Makefile:23-27` to `test: test-vim test-nvim`, removing the `&`/`wait` recipe; both suites run sequentially, and `make -j2 test` parallelizes them through the GNU make jobserver.
- Add `bench`, `bench-record`, and `bench-check` targets:
  - `bench` runs `bash bench/run.sh all` with `BENCH_OUT=bench/last.txt`.
  - `bench-record` runs `bench` then `python3 bench/check.py --record --input bench/last.txt --output bench/baseline.json`.
  - `bench-check` runs `bench` then `python3 bench/check.py --check --input bench/last.txt --baseline bench/baseline.json`.
- Add `check-changelog` running `python3 tools/check_changelog.py $(DATE)` and failing when `DATE` is unset.
- Rework `release` at `Makefile:37-46` to `release: check DATE`, then run `python3 tools/refresh_map.py`, `$(MAKE) test`, and `$(MAKE) generate-check`, then stage `tools/generate_map.py autoload/emoji_to_text/data.vim README.md NOTICE CHANGELOG.md` and commit `Release $(DATE)` only when something is staged.
- Keep `generate`, `generate-check`, `refresh-map`, `refresh-check`, `test-vim`, `test-nvim`, and the themis bootstrap at lines 34-35 unchanged.
- Update the `.PHONY` list at line 6 accordingly.
- Add `bench/last.txt` to `.gitignore`.

### Release Process And Workflow

Amended: the job runs on `ubuntu-latest` and installs the editors without a pinned runner image.

- Add `docs/RELEASING.md` describing the human process in order: confirm the pinned upstream tag is the intended one, add the `CHANGELOG.md` entry for the date in a normal commit on the default branch, run the Release workflow, and verify the tag and release.
- Rewrite `.github/workflows/release.yml`:
  - Trigger only `on: workflow_dispatch`, with inputs `date` (string, optional; defaults to the UTC current date) and `dry_run` (boolean, default `false`).
  - Remove the `on: push: tags: ["v*"]` trigger, the `pin-guard` job, and all `pin-held` logic.
  - Single job `release` on `ubuntu-24.04` with `permissions: contents: write` and `concurrency.group: release` and `cancel-in-progress: false`.
  - Steps in order: checkout the default branch with `fetch-depth: 0`; set up Python 3.12; install Vim `v9.2.1167` and Neovim `v0.12.5`; cache and install themis; resolve `DATE` from the input or `date -u +%F` and validate `YYYY-MM-DD`; configure the `github-actions[bot]` git identity; run `make check-changelog DATE=$DATE`; run `make release DATE=$DATE`; push `HEAD` to the default branch; force-move the tag with `git tag -f "$DATE"` and `git push -f origin "$DATE"`; then `gh release view "$DATE"` and either `gh release edit "$DATE" --title "$DATE" --notes-file /tmp/notes.md` or `gh release create "$DATE" --title "$DATE" --notes-file /tmp/notes.md`, where `/tmp/notes.md` comes from `make`-extracted `tools/check_changelog.py "$DATE" --print-section`.
  - When `dry_run` is true, run everything through `make release` but skip the push, the tag, and the release steps, and print the git diff.
- Delete `.github/workflows/refresh-upstream.yml`.
- The workflow never runs on a schedule or on a push; only `workflow_dispatch` triggers it.
- Every release step fails closed: a missing changelog entry, an unreachable upstream, a failed test, or a failed `generate-check` stops before any push or tag.

### CI Test Workflow

Amended: the `vim-old` leg was dropped and the editors are installed from the distribution and the pinned tarball.

- In `.github/workflows/test.yml`, change the behavior matrix at lines 23-30 to an explicit include list with an `editor`, a `target`, a `version`, and a `neovim` flag:
  - `vim` targeting `test-vim` at `v9.2.1167`.
  - `vim-old` targeting `test-vim` at the oldest feasible Vim 8.0.x, first attempt `v8.0.0000`.
  - `nvim` targeting `test-nvim` at `v0.12.5`.
- Change the run step at line 43 to `make ${{ matrix.target }}` and name the job with `matrix.editor`.
- Add a `bench-check` job on `ubuntu-24.04` that installs Vim `v9.2.1167`, Neovim `v0.12.5`, and Python 3.12, then runs `make bench-check`; gate it behind the behavior job with `needs: behavior`.
- Keep the `generate-check` and `refresh-check` jobs at lines 45-85 unchanged except for any version pins.
- If `v8.0.0000` cannot build on `ubuntu-24.04`, fall back in order: the oldest buildable 8.0.x patch, then run the `vim-old` leg on a container image that carries a Vim 8.0.x build; if no 8.0.x is obtainable, drop to the oldest buildable Vim and narrow the README floor to that version.

## Frontend And UI Requirements

- There is no graphical UI; the user-facing surfaces are the `:EmojiToText` command, `:help emoji-to-text`, `README.md`, `CHANGELOG.md`, `docs/RELEASING.md`, and the GitHub Release.
- The command prints no message on success; the only new messages are the non-UTF-8 message at `autoload/emoji_to_text.vim:76` and the non-modifiable message.
- Update `doc/emoji_to_text.txt` limits section to note that a buffer with `'nomodifiable'` set is left unchanged.
- Add to `README.md` after line 1 a Test workflow badge pointing at `https://github.com/efournier92/vim-emoji-to-text/actions/workflows/test.yml`.
- Add a `## Requirements` section to `README.md` stating: Vim 8.0 or newer (or the proven floor) with `+eval` and `+multi_byte`; Neovim at or above the CI-tested floor; no runtime dependencies; Python 3.8 or newer required only to build and test; `vim-themis` v1.7.0 required only for the behavior suite; a POSIX shell required only for local Makefile targets.
- Note in the README install section that manual `set runtimepath+=` installs need `:helptags doc` for `:help emoji-to-text`.
- Extend the README Development section at lines 55-57 to list `make -j2 test`, `make bench`, `make bench-check`, and a pointer to `docs/RELEASING.md`.

## Production Risks And Mitigations

Amended: the baseline is recorded on `ubuntu-latest` and the `vim-old` leg no longer exists.

- A refreshed dataset could introduce a collision or an unsafe name; mitigate because `generate_map.build_map` aborts on collisions, empty names, and names outside `[a-z0-9_+-]`, and because the release runs `make generate-check`.
- A failed refresh could leave a half-updated tree; mitigate with compute-first, write-last and temp-file-plus-`os.replace`, covered by an atomicity test.
- Force-moving a datestamp tag rewrites history for anyone who fetched the earlier tag; mitigate by documenting that same-day releases intentionally replace the prior cut and by keeping the tag input human-controlled.
- Force-pushing a tag can race a concurrent release; mitigate with `concurrency.group: release` and `cancel-in-progress: false`.
- The benchmark gate can be flaky across hosts; mitigate by recording `bench/baseline.json` on `ubuntu-24.04` with the pinned editor versions and by exposing `BENCH_TOLERANCE` for a one-off adjustment.
- Publishing a GitHub Release needs write access; mitigate with a job-scoped `permissions: contents: write`.
- `vim 8.0.0000` may not build on `ubuntu-24.04`; mitigate with the fallback ladder in the CI section and by narrowing the README floor if 8.0.x is unobtainable.
- A `gh release view` race could create a duplicate release; mitigate by treating an existing tag as the edit path and by the single-job design.
- Removing the scheduled refresh means a stale dataset can sit on `main` indefinitely; mitigate because the release path forces a refresh to the latest upstream tag, so no release can ship stale data.
- A crash between the four file writes could leave an inconsistent set; mitigate by ordering writes so `make generate-check` detects any mismatch and by documenting `git checkout -- <paths>` recovery in `docs/RELEASING.md`.

## Rollout Plan

1. Add the `&modifiable` guard in `autoload/emoji_to_text.vim` and its themis case.
2. Refactor `tools/refresh_map.py` for atomic writes and `NOTICE`, and add refresh unit tests.
3. Add `CHANGELOG.md`, `tools/check_changelog.py`, and `test/test_changelog.py`.
4. Add `bench/check.py`, `test/test_bench.py`, record `bench/baseline.json`, and add the `bench*` Makefile targets.
5. Make `test` portable and rework the `release` target and `.PHONY`; add `bench/last.txt` to `.gitignore`.
6. Update `README.md` (badge, requirements, helptags note, development) and `doc/emoji_to_text.txt`; add `docs/RELEASING.md`.
7. Update `.github/workflows/test.yml` for the `vim-old` leg and the `bench-check` job; delete `.github/workflows/refresh-upstream.yml`.
8. Rewrite `.github/workflows/release.yml` for the datestamp `workflow_dispatch` flow.
9. Run the full local gate, merge to `main`, then run the Release workflow for the 2026-10-08 datestamp and verify the tag, the release, and the notes.

## Test Plan

Test seams: the existing themis command seam in `test/convert.vim`; the Python unit seams in `test/test_refresh.py`, `test/test_generate.py`, and `test/test_encoding.py`; new `test/test_changelog.py` and `test/test_bench.py`; and the CI workflows as the integration seam for the release process.

Exact cases in `test/convert.vim`:

- Case 27, nomodifiable guard: set a line to `😀`, run `setlocal nomodifiable`, call `EmojiToText` inside a `try`/`catch`, assert no exception is thrown, assert the line still equals `😀`, and assert `getline` and the search register are unchanged.
- Case 28, modifiable control: after case 27, clear `nomodifiable` and assert a fresh `😀` line converts to `:grinning:`, proving the guard does not leak.
- All existing cases 1-26 and the two extra cases (`guard_double_load`, `api_convert_function`) must still pass unchanged under both editors.

Exact cases in `test/test_refresh.py` (add to the existing two):

- `render_pin` replaces all four `SOURCE_*` constants and leaves the rest of the file byte-identical.
- `render_notice` replaces an existing `Pinned revision:` line and appends one when absent.
- `render_readme` replaces an existing `Pinned dataset:` line and appends one when absent.
- Success path with a stubbed `fetch_tags` and `download_dataset` and a tiny dataset writes updated `generate_map.py`, `data.vim`, `README.md`, and `NOTICE` in a temporary repo root.
- Atomicity: stub `generate_map.build_map` to raise and assert `generate_map.py`, `data.vim`, `README.md`, and `NOTICE` are all byte-identical to their pre-call content.
- No-op path: when the resolved tag and commit equal the pin, nothing is written and the existing message is printed.
- `--dry-run` still writes nothing and prints the tag.

Exact cases in `test/test_generate.py`:

- All existing 14 cases must still pass; no changes required unless the in-process refactor moves a helper.

Exact cases in `test/test_changelog.py` (new):

- A file with `## [2026-10-08]` and a non-blank body returns exit 0.
- A file without the date returns exit 1.
- A file with the date heading and an empty body returns exit 1.
- A file where the date appears only under `## [Unreleased]` returns exit 1.
- `--print-section` returns exactly the section body for a present date and exits 1 for an absent date.
- An invalid date (`2026-10-8`, `today`) returns exit 2.

Exact cases in `test/test_bench.py` (new):

- The parser maps `exec editor=vim heavy lines=1000 reps=1 per_run_ms=113.417` to key `exec:vim:heavy:1000:per_run_ms` with value `113.417`.
- A check passes when every gated metric is within tolerance.
- A check fails, listing the key, when one gated metric exceeds `baseline * (1 + tolerance)`.
- A check fails when a gated metric is missing from the baseline.
- `--record` writes the expected JSON shape with `tolerance` and `metrics`.
- `BENCH_TOLERANCE` overrides the default tolerance.

Exact cases in `test/test_encoding.py`:

- The existing non-UTF-8 case still passes unchanged.

CI integration checks:

- `make check-changelog DATE=<today>` fails on a `main` that lacks the entry and passes once the entry is committed.
- The Release workflow with `dry_run: true` prints the diff and creates no tag or release.
- The Release workflow with a valid date commits `Release <DATE>`, moves the tag, and creates a GitHub Release whose notes equal the changelog section.
- A second Release run on the same date moves the tag to the new commit and updates the existing Release without creating a duplicate.
- The `vim-old` leg runs `make test-vim` and is green, or the fallback ladder is applied and the README floor is narrowed in the same change.

## Summary Of Changes

- Engine declines cleanly on a `nomodifiable` buffer with a message instead of raising `E21`.
- `tools/refresh_map.py` computes all new content first and writes it atomically, and updates `NOTICE` in addition to the pin, `README.md`, and the dataset.
- `Makefile:41` stages `NOTICE`; the `release` target takes `DATE` and runs `check-changelog` first.
- `CHANGELOG.md` added with `tools/check_changelog.py` and `test/test_changelog.py`; the release fails without an entry for the date.
- `bench/check.py`, `bench/baseline.json`, `test/test_bench.py`, and the `bench`, `bench-record`, `bench-check` targets add a performance gate with a 50 percent default tolerance.
- The Makefile `test` target drops `&`/`wait`; `make -j2 test` parallelizes.
- `README.md` gains a CI badge, a requirements section, a helptags note, and updated development commands; `doc/emoji_to_text.txt` notes the nomodifiable behavior.
- `docs/RELEASING.md` documents the human release process.
- `.github/workflows/test.yml` adds a `vim-old` floor leg and a `bench-check` job.
- `.github/workflows/refresh-upstream.yml` is deleted.
- `.github/workflows/release.yml` becomes a single human-triggered datestamp release with tag move, release create or update, and no scheduled or push trigger.
- `docs/GLOSSARY.md` records the release-domain terms.
- The 2026-10-08 release is cut through the new process.

## Verification Steps

1. `make generate-check` exits 0.
2. `make test` is green under Vim and Neovim; `make -j2 test` is green.
3. `python3 test/test_generate.py`, `python3 test/test_encoding.py`, `python3 test/test_refresh.py`, `python3 test/test_changelog.py`, and `python3 test/test_bench.py` all exit 0.
4. `python3 tools/refresh_map.py --dry-run` prints the latest upstream tag and writes nothing (`git status --porcelain` empty).
5. `make bench-check` passes against the committed baseline; a temporarily inflated baseline fails with the offending key.
6. `make check-changelog DATE=2026-10-08` passes only after the entry is committed.
7. Manual Vim check: open a `nomodifiable` scratch buffer with `😀`, run `:EmojiToText`, confirm the message and that the line is unchanged; clear the flag and confirm conversion works.
8. `git grep -n 'pin-held\|refresh-upstream'` returns nothing outside historical specs.
9. Run the Release workflow with `dry_run: true`; confirm no tag and no release are created.
10. Run the Release workflow for `2026-10-08`; confirm the tag points at the release commit, `gh release view 2026-10-08` shows the changelog section as notes, and the source archives are attached.
11. Re-run the same-day release after a new commit; confirm the tag moves and the release updates in place.
12. Confirm the repository has no scheduled workflow: `gh workflow list` shows only Test and Release.

## Assumptions And Defaults

- `GENERATOR_VERSION` in `tools/generate_map.py` stays a generator schema version (`0.1.0`) and is not tied to the release datestamp.
- `bench/baseline.json` is recorded on `ubuntu-24.04` with Vim `v9.2.1167` and Neovim `v0.12.5`, tolerance 0.5.
- The first `vim-old` pin attempt is `v8.0.0000`.
- The changelog entry is committed by a human on the default branch before the release workflow runs.
- `gh` is available on the release runner and authenticated by the workflow token.

## Open Questions

None. All frontier decisions were resolved during scoping on 2026-10-08.
