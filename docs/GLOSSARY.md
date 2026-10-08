# Glossary

Project-specific terms used across EmojiToText specs and docs. Each entry defines what the concept is, not what it does.

**Pin**

The set of upstream dataset constants recorded in `tools/generate_map.py`: `SOURCE_TAG`, `SOURCE_COMMIT`, `SOURCE_SHA256`, and `SOURCE_DATE`. _Avoid_: lock, version, revision (for the constant set as a whole).

**Dataset**

The generated map shipped in `autoload/emoji_to_text/data.vim`, derived from one pinned `iamcal/emoji-data` revision. _Avoid_: catalog, table, dictionary.

**Refresh**

The release-time action that resolves the latest upstream tag, rewrites the pin, regenerates the dataset, and updates `README.md` and `NOTICE`. _Avoid_: sync, update, bump (for the full action).

**Cut A Release**

The human-triggered `workflow_dispatch` run that refreshes, tests, enforces the changelog, commits on the default branch, moves the datestamp tag, and creates or updates the GitHub Release. _Avoid_: publish, deploy, ship.

**Datestamp Version**

The release identifier, a bare UTC date in `YYYY-MM-DD` form, used as both the git tag and the GitHub Release name. _Avoid_: semver tag, release number, build number.

**Changelog Entry**

A `## [YYYY-MM-DD]` section in `CHANGELOG.md` with at least one non-blank line, describing the changes in that datestamp release. _Avoid_: release note (for the changelog section itself).

**Benchmark Baseline**

The committed `bench/baseline.json` recording reference per-metric results, captured on the pinned CI runner image. _Avoid_: snapshot, golden file.

**Perf Gate**

The `make bench-check` comparison that fails when a gated benchmark metric exceeds its baseline by more than the tolerance. _Avoid_: budget, threshold (for the check as a whole).
