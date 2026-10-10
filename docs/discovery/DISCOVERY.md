# Discovery

One line per finding, decision, assumption, trap, question, or outcome. Newest first. Evidence required.
Scope tokens: autoload, docs, plugin, readme, test

## Entries

- D-20261010-06 | 2026-10-10 | [trap] | docs | The README's fenced `Latest Pinned Dataset` line is machine-parsed; change its format without updating `tools/refresh_map.py` and refresh appends a stray pin line. | `tools/refresh_map.py:30`
- D-20261010-01 | 2026-10-10 | [decision] | plugin | `:EmojiToText` respects a range (visual or `:n,m`); no range converts the whole buffer, still one undo step. | `test/convert.vim:283`
- D-20261010-02 | 2026-10-10 | [decision] | autoload | Consecutive emoji emit adjacent shortcodes with no separator on purpose: Slack parses `:a::b:` as two, and a space would inject irreversible bytes. | `test/convert.vim:33`
- D-20261010-03 | 2026-10-10 | [decision] | readme | README Vim floor is 9.1, the distro Vim `ubuntu-latest` installs; the prior 8.0 claim was proven once but never executed in CI. | `.github/workflows/test.yml:24`
- D-20261010-05 | 2026-10-10 | [outcome] | test | Range change verified: `make test` green 36/36 under Vim 9.2 and Neovim 0.12.5, no regressions. | `make test`
