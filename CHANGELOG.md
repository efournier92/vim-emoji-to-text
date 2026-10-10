# Changelog

All changes to this project are documented in this file. Releases use `YYYY-MM-DD` datestamp versions, and each entry lists what changed since the previous cut.

## [Unreleased]

Nothing yet.

## [2026-10-10]

### Added

- Added range support to `:EmojiToText`: no range converts the whole buffer, and a range such as `:2,5EmojiToText` or a visual selection converts only those lines.

### Changed

- Raised the documented Vim floor to 9.1 and the Neovim floor to v0.12.5, the versions CI actually installs.
- Pinned the CI runners to `ubuntu-24.04` so the documented Vim 9.1 floor stays tested.

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
- The performance gate now compares same-run ratios instead of an absolute wall-clock baseline, so it no longer depends on the host CPU speed.
- CI now uses `ubuntu-latest` and installs Vim from the distribution and Neovim from the pinned prebuilt tarball, replacing `rhysd/action-setup-vim` so the workflows no longer follow a fixed runner image.

### Removed

- Removed the `vim-old` CI leg; the Vim 8.0 floor was proven at this release.

### Fixed

- Fixed the `E21` failure on `'nomodifiable'` buffers by leaving them unchanged.
- Fixed `NOTICE` pin drift by regenerating it during every dataset refresh.
- The noisy `load:*:delta_ms` gate was replaced by a measured `source_data_ms` ratio, and missing benchmark metrics now fail instead of passing silently.
- The empty-buffer benchmark metric is no longer gated, and the gate now warns when recorded editor versions drift.
- The load-time source ratio is no longer gated (recorded only), because it tracks the editor build's loading speed and would make the gate follow the Vim release.
