# EmojiToText

[![Test](https://github.com/efournier92/vim-emoji-to-text/actions/workflows/test.yml/badge.svg)](https://github.com/efournier92/vim-emoji-to-text/actions/workflows/test.yml)

A Vim 8+ and Neovim plugin that replaces fully-qualified emoji in the current buffer with Slack-style `:shortcode:` text, for example `:grinning:`.

Works in Vim 8.0+ and Neovim from one pure-Vimscript codebase with no runtime dependencies.

## Requirements

- Vim 8.0 or newer with `+eval` and `+multi_byte`.
- Neovim at or above the CI-tested floor.
- No runtime dependencies.
- Python 3.8 or newer, required only to build and test.
- `vim-themis` v1.7.0, required only for the behavior suite.
- A POSIX shell, required only for local Makefile targets.

## Install

EmojiToText is a standard runtimepath plugin: no build step, no runtime dependencies, and no editor-specific files. It works with any Vim or Neovim plugin manager, including vim-plug, Vundle, Pathogen, dein.vim, minpac, lazy.nvim, packer.nvim, and Vim's native `packages` (`:packadd`), or a manual `set runtimepath+=/path/to/vim-emoji-to-text`. A manual `set runtimepath+=` install also needs `:helptags doc` so that `:help emoji-to-text` works.

With vim-plug, add this and run `:PlugInstall`:

    Plug 'efournier92/vim-emoji-to-text'

## Usage

Run the command to convert the whole buffer.

    :EmojiToText

The plugin ships no default mapping, so bind your own.

    nnoremap <leader>et :EmojiToText<CR>

## What It Converts

- Fully-qualified emoji, including zero-width-joiner sequences such as `:man-woman-girl:`.
- Country flags such as `:flag-us:`.
- Keycaps such as `:one:`.
- Skin-tone variants, with the tone dropped: a thumbs-up with light skin becomes `:+1:`.

## What It Leaves Alone

- Non-qualified forms such as a bare `❤` or `©`.
- Unknown emoji.
- Skin-tone modifiers on their own.
- Text and code with no emoji.

## Limits

- The command acts on the whole buffer; there is no range or selection mode.
- It never runs automatically.
- There is no reverse conversion from shortcode back to emoji.

## Pinned Dataset

The map is generated from a pinned `iamcal/emoji-data` revision.

Pinned dataset: iamcal/emoji-data v16.0.0 (2771d0b1b3af25c069086e68e38f901c3dda8bdf)

## Help

After installing, open the documentation with `:help emoji-to-text`.

## Development

Run the checks with `make generate-check`, `make test`, and `make refresh-check`. `make test` runs the vim-themis behavior specs under both Vim and Neovim. CI runs the behavior specs on the distribution's Vim and on Neovim v0.12.5.

Run both suites in parallel with `make -j2 test`. Run the benchmarks with `make bench` and gate them with `make bench-check`.

See `docs/RELEASING.md` for the release process.

## License

MIT. See `LICENSE` and `NOTICE`.
