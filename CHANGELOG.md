# Changelog

All changes to this project are documented in this file. Releases use `YYYY-MM-DD` datestamp versions, and each entry lists what changed since the previous cut.

## [Unreleased]

Nothing yet.

## [2026-10-08]

### Added

- Added `CHANGELOG.md` and the tag-time check in `tools/check_changelog.py` that blocks a release without an entry for the date.
- Added `docs/RELEASING.md` describing the human release process step by step.
- Added the benchmark gate in `bench/check.py` with a committed baseline and a `make bench-check` target.
- Added a `vim-old` leg to the CI test workflow to guard the oldest supported Vim.

### Changed

- Changed `make test` to run both suites sequentially, dropping the `&`/`wait` recipe so it works under a POSIX shell.
- Changed the dataset refresh to compute every file before writing and to update `NOTICE` alongside the pin, the dataset, and the README.
- Refreshed the README with a CI badge and updated Requirements and Development sections.
- The performance gate now compares same-run ratios instead of an absolute wall-clock baseline, so it is host-independent.

### Fixed

- Fixed the `E21` failure on `'nomodifiable'` buffers by leaving them unchanged.
- Fixed `NOTICE` pin drift by regenerating it during every dataset refresh.
- The noisy `load:*:delta_ms` gate was replaced by a measured `source_data_ms` ratio, and missing benchmark metrics now fail instead of passing silently.
