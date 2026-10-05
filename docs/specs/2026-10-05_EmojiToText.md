# EmojiToText: Vim Plugin Spec

This spec turns the ad-hoc `EmojiToText.vim` mapping into a vim-plug-installable Vim plugin.
The plugin replaces emoji in the current buffer with colon-wrapped lowercase shortcodes, for example `:grinning:`, matching Slack's shortcode style.
The user's expected mapping is notated in `EmojiToText.vim`, which is the reference for this work.
The draft sentence "between columns" was clarified during scoping as "a leader shortcut applied to the whole open buffer", not blockwise or column-wise editing.
The truncated sentence "Also, research to ensure" was clarified as "ensure this exact plugin does not already exist"; the existence check and its counterexample are recorded under Current State and Non-Goals.

## Context And Motivation

- The current script converts emoji to `::lowercase_name::` by looping over a hand-written dictionary and running one `:s` per entry (`EmojiToText.vim:106-110`).
- That approach is slow (one full-buffer scan per dictionary key), fragile (no regex escaping, no longest-match ordering for multi-codepoint sequences), and limited to roughly 100 base emoji.
- The user wants a shareable plugin installed with vim-plug that works in both Vim 8+ and Neovim.
- The desired output changed from `::lowercase_name::` to `:name:` for Slack parity, so `EmojiToText.vim` is a mapping reference for names, not a format reference.
- A Neovim-only counterexample exists (`StefanBartl/emojis.nvim`, Lua, MIT), which is why this spec builds a small Vimscript plugin instead of porting that one; see Non-Goals.
- Emoji names change over time, so the map is refreshed from the latest upstream release tag when a new plugin version is cut, and the repo keeps exactly one dataset artifact, updated in place.

## Glossary

**Emoji**

A user-perceived pictograph, possibly a sequence of several Unicode code points, including a base, a variation selector, a zero-width joiner, a skin-tone modifier, or tag characters.
_Avoid_: icon, glyph, symbol.

**Fully-Qualified Form**

The canonical emoji code point sequence, including U+FE0F where Unicode requires it for emoji presentation.
_Avoid_: qualified form, canonical form.

**Non-Qualified Form**

The same emoji without its optional U+FE0F, as recorded in iamcal's `non_qualified` field.
_Avoid_: bare form, unqualified form.

**Skin-Tone Variant**

A base emoji followed by one of U+1F3FB through U+1F3FF.
_Avoid_: toned emoji, modifier.

**Shortcode**

The colon-wrapped lowercase name produced by the plugin, for example `:grinning:`.
_Avoid_: label, tag, code, slug.

**Map**

The generated table from fully-qualified emoji sequences to shortcode names, shipped in `autoload/emoji_to_text/data.vim`.
_Avoid_: dictionary, catalog, table (when the generated artifact is meant).

## Current State

- The repo is not a git repository, has no `docs/` file tree beyond this spec, no tests, no plugin manifest, and no README.
- `EmojiToText.vim:2-103` defines `s:emoji_to_label`, a hand-written dictionary of about 100 emoji to lowercase names such as `grinning_face`.
- `EmojiToText.vim:106-110` defines `ConvertEmojiToText()`, which loops `items(s:emoji_to_label)` and runs `execute '%s/'.emoji.'/::'.label.'::/g'` for each entry.
- `EmojiToText.vim:108` interpolates the emoji directly into the pattern with no escaping, so any regex metacharacter in a key would break the pattern.
- `EmojiToText.vim:113` installs a default `nnoremap <F5>` mapping; the new plugin ships no default mapping.
- `EmojiToText.vim` keys are a mix of single code points and one variation-selector sequence (`☹️` at line 40), so the existing script does not guarantee that longer sequences win.
- `EmojiToText_EXAMPLE.vim:1-9` is a five-entry subset of the same dictionary, used only as an example.
- `emoji.bash:1-1847` holds 1845 entries in `:UPPER_SNAKE:` form.
- `emoji.bash:67` is malformed JSON, `"☹️"": ":FROWNING_FACE:",` (an extra quote), so the file cannot be parsed by a strict JSON reader.
- `emoji.bash` also has a key with a trailing space, `'☺️ '`, and 695 multi-codepoint keys.
- `Emoji.md:1-6` records one pasted emoji and two `U1F60A` notes; it is scratch, not a data source.
- External prior art exists: `StefanBartl/emojis.nvim` implements `:Emojis replace %` for emoji to `:name:` in Neovim, in about 4.7k lines of Lua, hard-depends on `lib.nvim`, and requires Neovim 0.9+.

## Goals

- Ship a vim-plug-installable plugin that converts the emoji in the current buffer to Slack-style `:name:` shortcodes.
- Ship a generated map from a single canonical dataset (`iamcal/emoji-data`) instead of the hand-written dictionaries.
- Convert fully-qualified emoji only, including zero-width-joiner sequences, flags, keycaps, and skin-tone variants.
- Drop skin-tone modifiers, so a toned emoji converts to its base shortcode.
- Work in both Vim 8+ and Neovim from one pure-Vimscript codebase with no runtime dependencies.
- Expose exactly one user-facing command, `:EmojiToText`, with no default key mapping.
- Keep the generated data reproducible from a pinned dataset revision, refreshed from upstream at release time.

## User Stories

1. As a writer, I want to paste a paragraph full of emoji and run one command, so that every emoji becomes a Slack-style shortcode I can paste into Slack.
2. As a writer, I want the whole current buffer converted, so that I do not have to select a region first.
3. As a writer, I want to assign my own leader mapping to `:EmojiToText`, so that the plugin does not collide with my existing keys.
4. As a writer, I want a pasted zero-width-joiner family emoji to convert as one unit, so that I do not get a partial shortcode followed by leftover characters.
5. As a writer, I want a flagged country emoji to become `:flag-us:` style output, so that it matches Slack.
6. As a writer, I want a keycap emoji such as `1️⃣` to become `:one:`, so that numeric keycaps round-trip.
7. As a writer, I want a skin-toned emoji such as `👍🏻` to become `:+1:`, so that the tone is dropped rather than emitted as an unsupported code.
8. As a writer, I want a bare typographic character such as `©` to remain unchanged, so that prose and code are not rewritten unexpectedly.
9. As a writer, I want an unrecognized emoji to remain unchanged, so that the command never destroys text it cannot name.
10. As a writer, I want to undo the whole conversion with a single `u`, so that a mistaken run is cheap to reverse.
11. As a writer, I want running the command twice to change nothing, so that it is safe to run again.
12. As a writer, I want the command to leave my search pattern and jump list intact, so that it does not disturb navigation state.
13. As a plugin author, I want the emoji map generated from a pinned dataset revision, so that output is reproducible.
14. As a plugin author, I want the generator to fail loudly on collisions or empty names, so that bad data never reaches the shipped map.
15. As a plugin author, I want CI to regenerate the map and fail on a diff, so that the committed map cannot silently drift from the dataset.
16. As a plugin author, I want tests to run under both Vim and Neovim, so that the cross-editor promise is verified.
17. As a packager, I want a prebuilt map committed to the repo, so that installing with vim-plug needs no network or build step.
18. As a help reader, I want `:help emoji-to-text` to document the command, options, and limits.
19. As a Vim 8 user, I want the plugin to load without Neovim-only APIs, so that it works in my editor.
20. As a maintainer, I want the prior-art overlap stated, so that the reason for a separate plugin is explicit.
21. As a maintainer, I want the plugin to refresh from the latest upstream release tag when I cut a new version, so that each release ships the newest names.
22. As a maintainer, I want exactly one dataset artifact in the repo, overwritten in place on refresh, so that there is no versioned-snapshot sprawl.
23. As a maintainer, I want the regenerated map, the data header, and the README revision line to change in one commit, so that the package always reflects the shipped dataset.
24. As a maintainer, I want the release to stop if refresh or tests fail, so that a stale dataset never ships silently.

## Non-Goals

- No automatic conversion on paste, insert, or buffer write; conversion is explicit via `:EmojiToText`.
- No interception of terminal or GUI paste (Cmd-V, Ctrl-Shift-V, middle-click); the user runs the command after pasting.
- No default key mapping; the user wires their own.
- No reverse conversion from shortcode back to emoji.
- No visual-range or partial-buffer conversion; the command always acts on the whole buffer.
- No preservation of skin-tone modifiers.
- No conversion of non-qualified (VS16-less) forms.
- No emoji picker, completion, concealment, quickfix listing, counting, project-wide search, or Unicode toolkit.
- No Neovim Lua port and no port of `StefanBartl/emojis.nvim`; that project already covers Neovim with a larger feature set.
- No new runtime dependencies; the plugin must load with `:set rtp+=` alone.

## Prerequisites

- Vim 8.0 or newer, or Neovim, compiled with `+eval` and `+multi_byte`.
- Python 3.8 or newer for the map generator (build time only, not runtime).
- `vim-themis` v1.7.0 or a compatible version for tests (development only, not shipped to users).
- A git remote so that `Plug 'USER/emoji-to-text'` resolves; the author and remote are placeholders to fill at publish time.
- Generated `autoload/emoji_to_text/data.vim` committed to the repo so users need no network access.

## Design Principles

- One dataset, one generated artifact, one command.
- Fully-qualified keys only; shortest correct output wins.
- Longest sequence first, so a zero-width-joiner sequence never loses to its prefix.
- Lazy load; the 3781-entry map is read only when the command first runs.
- No runtime dependencies and no Neovim-only APIs.
- Fail the build, never the user, on bad data.

## Backend Requirements

### Repository Layout

Create this layout at the repo root.

- `plugin/emoji_to_text.vim`: guard variable, command definition.
- `autoload/emoji_to_text.vim`: conversion engine and pattern cache.
- `autoload/emoji_to_text/data.vim`: generated map, marked do-not-edit.
- `tools/generate_map.py`: Python 3 generator, holding the pin constants.
- `tools/refresh_map.py`: resolves the latest upstream release tag, rewrites the pin constants, and regenerates the map in place (release only).
- `test/convert.vim`: themis behavior specs.
- `doc/emoji_to_text.txt`: Vim help file with tag `*emoji-to-text*`.
- `Makefile`: `generate`, `generate-check`, `refresh-map`, `test`, `test-vim`, `test-nvim`, `release`.
- `README.md`: install and usage, including the pinned dataset revision line.
- `LICENSE`: MIT.
- `NOTICE`: dataset attribution.
- `.github/workflows/test.yml`: CI matrix.
- `.github/workflows/release.yml`: tag-triggered guard job and a manual release job.
- No committed JSON snapshot and no versioned dataset directories: `autoload/emoji_to_text/data.vim` is the single dataset artifact.

### Dataset Generation

- Source: `https://raw.githubusercontent.com/iamcal/emoji-data/<SOURCE_COMMIT>/emoji.json`.
- Pin `SOURCE_TAG = v16.0.0`, `SOURCE_COMMIT = 2771d0b1b3af25c069086e68e38f901c3dda8bdf`, and the as-of date 2026-10-05.
- Verify the downloaded bytes against sha256 `1d602e65be88772bf8cc368ce16b855d719eeddbafe128d471b80203f494d29f`; abort on mismatch.
- The pinned revision has 1911 source entries and yields 3781 map keys.
- Accept `--input PATH` to generate from a local JSON file without the network, and `--output PATH` defaulting to `autoload/emoji_to_text/data.vim`.
- Support `--check`, which regenerates to a temp path and exits non-zero if the committed output differs.
- Use only the Python standard library (`argparse`, `json`, `hashlib`, `urllib.request`, `re`, `pathlib`).

### Dataset Refresh Policy

- Refresh only when cutting a new plugin version; there is no scheduled job.
- `tools/refresh_map.py` queries the tags of `iamcal/emoji-data` (the repo has tags such as `v16.0.0` and no GitHub release objects), selects the highest semver tag, and resolves that tag's commit.
- It downloads `emoji.json` at that commit, computes the sha256, and rewrites `SOURCE_TAG`, `SOURCE_COMMIT`, and the sha256 in `tools/generate_map.py`.
- It then runs the generator, overwriting `autoload/emoji_to_text/data.vim` in place, and refreshes the README revision line.
- If the upstream tag is unchanged since the last pin, refresh is a no-op and reports so.
- The repo holds exactly one dataset artifact at a time: the committed `data.vim`. Do not commit the JSON, and do not keep per-version copies.
- The release procedure is: refresh, run both test suites, commit the regenerated map plus pin bump in one commit, then create the tag.
- A release stops if refresh or either test suite fails.
- `.github/workflows/release.yml` re-resolves the upstream tag on tag creation and fails if the committed pin is not the latest, unless the release commit message contains the marker `pin-held`.
- This spec records the pin as of 2026-10-05; the spec is not rewritten on each refresh. The data header and README line carry the live revision.

The generator algorithm, in order.

1. Load the dataset array.
2. For each entry, compute the canonical name: use `short_name`, except for entries whose `category` is `Flags`, where the first `short_names` alias starting with `flag-` wins.
3. Skip entries whose `category` is `Component` (the five standalone skin-tone modifiers).
4. Register the entry's `unified` sequence, mapped to the canonical name.
5. For each value in the entry's `skin_variations`, register that `unified` sequence, mapped to the same canonical name (the tone is dropped).
6. Do not register `non_qualified` sequences.
7. Parse each sequence by splitting on `-` and reading each token as hexadecimal; reject an unparseable token.
8. Accumulate collisions; if one sequence maps to two different names, abort with both names printed.
9. Reject any empty name.
10. Sort output keys by their code point tuple, ascending, for a deterministic file.

Expected results, verified against the pinned revision on 2026-10-05: 3781 unique keys, zero collisions, longest key 10 code points, and no name containing characters outside `[a-z0-9_+-]`.

Representative mappings to assert in the generator's own self-check.

| Emoji Sequence | Code Points | Shortcode |
| --- | --- | --- |
| grinning face | 1F600 | `:grinning:` |
| man-woman-girl | 1F468-200D-1F469-200D-1F467 | `:man-woman-girl:` |
| flag United States | 1F1FA-1F1F8 | `:flag-us:` |
| flag United Kingdom | 1F1EC-1F1E7 | `:flag-gb:` |
| flag China | 1F1E8-1F1F3 | `:flag-cn:` |
| thumbs up, light skin | 1F44D-1F3FB | `:+1:` |
| waving hand, medium skin | 1F44B-1F3FD | `:wave:` |
| red heart with VS16 | 2764-FE0F | `:heart:` |
| keycap one | 0031-FE0F-20E3 | `:one:` |
| keycap asterisk | 002A-FE0F-20E3 | `:keycap_star:` |
| smiley frowning face | 2639-FE0F | `:white_frowning_face:` |
| copyright sign with VS16 | 00A9-FE0F | `:copyright:` |

### Data Module

- `autoload/emoji_to_text/data.vim` starts with `scriptencoding utf-8` and a header comment naming the source URL, `SOURCE_TAG`, `SOURCE_COMMIT`, the sha256, the refresh date, the entry count, and the generator version.
- The module holds one script-local dictionary `s:map` whose keys are literal emoji strings (fully-qualified) and whose values are bare names without colons, for example `'😀': 'grinning'`.
- The module exposes `function! emoji_to_text#data#map() abort` returning `s:map`.
- The file is generated and committed; the header states "Generated by tools/generate_map.py, do not edit".
- On refresh the file is overwritten in place; it is the only dataset artifact in the repo.

### Conversion Engine

`autoload/emoji_to_text.vim` holds the engine. The following is a prototype-sourced shape, decisions captured as of 2026-10-05.

```vim
let s:map = {}
let s:pattern = ''

function! s:build_pattern() abort
  " Sort by byte length descending: if one key is a prefix of another,
  " the longer key has strictly more bytes, so longest-first is guaranteed.
  let l:keys = sort(keys(s:map), {a, b -> strlen(b) - strlen(a)})
  let l:alts = map(copy(l:keys), 'escape(v:val, ''\\*[]~^$.'')')
  let s:pattern = '\%(' . join(l:alts, '\|') . '\)'
endfunction

function! s:replace_match(match) abort
  let l:name = get(s:map, a:match, '')
  return empty(l:name) ? a:match : ':' . l:name . ':'
endfunction

function! emoji_to_text#convert() abort
  if empty(s:map)
    let s:map = emoji_to_text#data#map()
    call s:build_pattern()
  endif
  let l:pos = getcurpos()
  keeppatterns silent! execute '%s/' . s:pattern . '/\=s:replace_match(submatch(0))/ge'
  call setpos('.', l:pos)
endfunction
```

Requirements the snippet must satisfy.

- Build the pattern once and cache it in a script-local variable.
- Order alternatives longest-first by byte length, so a prefix never wins.
- Escape backslash, `*`, `[`, `]`, `~`, `^`, `$`, and `.` in every key.
- Wrap each replacement in single colons and return the original text when a match has no name.
- Use one `:%s` invocation so the conversion is a single undo step.
- Use `keeppatterns` so the search register is unchanged.
- Restore the cursor with `getcurpos()` and `setpos('.', ...)`.
- Load the data module and decode the file as UTF-8.

### Command Surface

- Define `command! -bar EmojiToText call emoji_to_text#convert()` in `plugin/emoji_to_text.vim`.
- Guard double loading with `g:loaded_emoji_to_text`.
- Ship no mapping. Document an example mapping in help and README, such as `nnoremap <leader>et :EmojiToText<CR>`.
- Ignore any range silently, or reject a range with a clear error; the chosen behavior is to ignore it and always act on the whole buffer.

### Naming And Canonicalization Rules

- Canonical name is `short_name`, with the `flag-` alias preference for the `Flags` category.
- Names are emitted lowercase with underscores, plus `+` where the dataset uses it, for example `:+1:`.
- Skin-tone modifiers are dropped, and the variant sequence maps to the base shortcode.
- The five standalone modifier entries are excluded, so a lone `🏼` is left unchanged.
- Obsolete entries are included because they still carry names and produced no collisions.

## Frontend And UI Requirements

There is no graphical UI. The user-facing surface is only the `:EmojiToText` command and `:help emoji-to-text`.
The command prints no message on success and makes one reversible undo step.
Document, in help and README, that the command converts only fully-qualified emoji, drops skin tones, leaves bare typographic characters alone, and does not run automatically.

## Production Risks And Mitigations

- Regex alternation over 3781 keys may be slow on very large buffers; mitigate by building the pattern once per session, doing a single pass, and documenting that the command is explicit.
- Vim regex alternation uses the first matching alternative; mitigate with byte-length-descending ordering and a dedicated zero-width-joiner test.
- ASCII metacharacters in keycap keys, especially `*️⃣`; mitigate with the escape list above and a keycap test.
- Encoding drift in the generated file; mitigate with `scriptencoding utf-8` and tests under both editors.
- Dataset drift; mitigate with a pinned tag and commit, a sha256 check, a CI `generate-check`, and the release refresh procedure.
- A refresh changes names or key counts between releases; mitigate by treating the map as the single artifact, running both suites after refresh, and recording the pin in the data header and README.
- Upstream tag resolution fails or the tag format changes; mitigate by aborting the release, never generating from an unpinned revision.
- Dataset licensing; mitigate by shipping MIT plus a `NOTICE` with iamcal attribution.
- `vim-themis` is an external dev dependency with Neovim quirks; mitigate by pinning v1.7.0 and documenting `THEMIS_VIM=nvim THEMIS_ARGS="-e --headless"`.
- Silent data corruption during generation; mitigate by aborting on collisions, empty names, and unparseable code points.

## Rollout Plan

1. Initialize the git repo, add `LICENSE` (MIT), `NOTICE`, and `.gitignore`.
2. Add `tools/generate_map.py` and run it to produce `autoload/emoji_to_text/data.vim`.
3. Add `autoload/emoji_to_text.vim` and `plugin/emoji_to_text.vim`.
4. Add `test/convert.vim` and the `Makefile` targets; get both editors green.
5. Add `doc/emoji_to_text.txt`, `README.md`, and the CI workflow.
6. Add `tools/refresh_map.py` and `.github/workflows/release.yml`; dry-run the refresh against `v16.0.0`.
7. Verify install with vim-plug from a clean config on Vim and Neovim.
8. Cut `v0.1.0` through the refresh-then-release procedure.

## Test Plan

Test seam: the `:EmojiToText` command end to end on a scratch buffer, using vim-themis specs in `test/convert.vim`, run once with Vim and once with Neovim.
Each spec opens a scratch buffer, sets the lines, runs `:EmojiToText`, and asserts the resulting lines.
Runner commands are exact.

- `make test-vim`: `THEMIS_VIM=vim THEMIS_ARGS="-e -s" <themis>/bin/themis test/`
- `make test-nvim`: `THEMIS_VIM=nvim THEMIS_ARGS="-e --headless" <themis>/bin/themis test/`
- `make test`: runs both.
- `make generate-check`: `python3 tools/generate_map.py --check`.
- `make refresh-check`: `python3 tools/refresh_map.py --dry-run`, which prints the selected upstream tag without writing.

Exact cases in `test/convert.vim`.

1. Single emoji: `😀` becomes `:grinning:`.
2. Multiple per line: `😀😀` becomes `:grinning::grinning:`.
3. Adjacent text: `hi😀there` becomes `hi:grinning:there`.
4. Multi-line buffer: every line is converted, not just the cursor line.
5. Zero-width-joiner family: `👨‍👩‍👧` becomes `:man-woman-girl:`, proving longest match.
6. Couple sequence: `💑` becomes `:man-heart-man:`.
7. Skin tone dropped: `👍🏻` becomes `:+1:` and `👋🏽` becomes `:wave:`.
8. Bare modifier left alone: `🏼` is unchanged.
9. Country flag: `🇺🇸` becomes `:flag-us:` and `🇨🇳` becomes `:flag-cn:`.
10. Keycap digit: `1️⃣` becomes `:one:`.
11. Keycap asterisk: `*️⃣` becomes `:keycap_star:`, exercising metacharacter escaping.
12. Keycap hash: `#️⃣` becomes `:hash:`.
13. Variation selector: `❤️` becomes `:heart:`.
14. Non-qualified form untouched: bare `❤` is unchanged, and `©` is unchanged.
15. Unknown input untouched: a code point absent from the map is left byte-identical.
16. Idempotency: running `:EmojiToText` twice leaves the second run's buffer unchanged.
17. Undo: after conversion, one `u` restores the original buffer exactly.
18. No-op safety: a buffer with no emoji is unchanged and raises no error.
19. Empty buffer: no error.
20. Search register preserved: `@/` is unchanged after conversion.
21. Name containing plus: `👍` becomes `:+1:`.
22. Data load: `emoji_to_text#data#map()` returns a non-empty dictionary in both editors.
23. Generator determinism, in `make generate-check`: running twice yields a byte-identical file.
24. Refresh selection, in `make refresh-check`: the dry run selects the highest semver tag and writes nothing.

## Summary Of Changes

- Add `tools/generate_map.py` producing a 3781-entry map from pinned `iamcal/emoji-data` `v16.0.0`.
- Add `tools/refresh_map.py` and `.github/workflows/release.yml` for release-time refresh from the latest upstream tag.
- Add generated `autoload/emoji_to_text/data.vim` using fully-qualified keys only, overwritten in place on refresh.
- Add `autoload/emoji_to_text.vim` with longest-first, single-pass, single-undo conversion.
- Add `plugin/emoji_to_text.vim` defining `:EmojiToText` with no default mapping.
- Add `test/convert.vim` (themis) and `Makefile` targets for Vim, Neovim, and generation checks.
- Add `doc/emoji_to_text.txt`, `README.md`, `LICENSE` (MIT), `NOTICE`, and CI.
- Initialize git and publish so `Plug 'USER/emoji-to-text'` works.

## Verification Steps

1. `python3 tools/generate_map.py --check` exits 0.
2. `python3 tools/refresh_map.py --dry-run` prints the highest upstream tag and writes nothing.
3. `make test-vim` is green.
4. `make test-nvim` is green.
5. Manual Vim check: open a scratch file, paste `😀 👨‍👩‍👧 👍🏻 🇺🇸 1️⃣ ❤️ ©`, run `:EmojiToText`, confirm `:grinning: :man-woman-girl: :+1: :flag-us: :one: :heart: ©`, then press `u` and confirm the original returns.
6. Manual Neovim check mirrors step 5.
7. Clean-install check: in a throwaway config with vim-plug, `Plug 'USER/emoji-to-text'`, run `:PlugInstall`, confirm `:EmojiToText` exists and `:help emoji-to-text` opens.
8. Release guard check: on a test tag, confirm the release workflow fails when the committed pin is behind upstream and passes when it matches.
9. Run the Markdown linter on this spec before sign-off.

## Open Questions

None. All frontier decisions were resolved during scoping.
