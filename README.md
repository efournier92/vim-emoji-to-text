# EmojiToText

[![Test](https://github.com/efournier92/vim-emoji-to-text/actions/workflows/test.yml/badge.svg)](https://github.com/efournier92/vim-emoji-to-text/actions/workflows/test.yml)

## Purpose

- Vim plugin that replaces fully-qualified emoji in the current buffer with Slack-style `:shortcode:` text.
  - Example: 😀 becomes `:grinning:`.
- Works in Vim 9.1+ and Neovim v0.12.5+ from a unified pure-Vimscript codebase with no runtime dependencies.

## Requirements

- Vim 9.1 or newer with `+eval` and `+multi_byte`.
- Neovim v0.12.5 or newer.
- Editor running with `encoding=utf-8` *(the command declines otherwise)*.
- No runtime dependencies.
- Python 3.8 or newer (CI tests 3.12). *(Only to build and test)*.
- `vim-themis` v1.7.0. *(Only to run the behavior suite)*.
- A POSIX shell (bash for bench targets). *(Only for local Makefile targets)*.

## Install

### Support

- `EmojiToText` is a standard runtimepath plugin.
  - No mandatory build step.
  - No runtime dependencies.
  - No editor-specific files.
- It works with any Vim or Neovim plugin manager, including:
  - `vim-plug`
  - `Vundle`
  - `Pathogen`
  - `dein.vim`
  - `minpac`
  - `lazy.nvim`
  - `packer.nvim`
  - Vim's native `packages` (`:packadd`)
  - manual `set runtimepath+=/path/to/vim-emoji-to-text`
    - Also requires `:helptags doc` so that `:help emoji-to-text` works.

### Example

#### Using `vim-plug`

- Add `Plug 'efournier92/vim-emoji-to-text'`.
- Run `:PlugInstall`.

#### Using `lazy.nvim`

- Add `{ 'efournier92/vim-emoji-to-text' }` to your plugin spec.

## Uninstall

- Remove the plugin entry from your manager, or drop the `runtimepath` addition.
- Run `:helptags doc` if you installed it manually.

## Usage

- Run `:EmojiToText` to convert the whole buffer, or give it a range such as `:2,5EmojiToText` or a visual `:'<,'>EmojiToText` to convert only those lines.
- The plugin ships no default mapping, so bind your own.
  - `nnoremap <leader>emo :EmojiToText<CR>` for Normal mode.
  - `xnoremap <leader>emo :EmojiToText<CR>` for a visual selection.

## What It Converts

- Fully-qualified emoji, including zero-width-joiner sequences such as `:man-woman-girl:`.
- Country flags such as `:flag-us:`.
- Keycaps such as `:one:`.
- Skin-tone variants, with the tone dropped.

## What It Leaves Alone

- Non-qualified forms such as a bare `❤` or `©`.
- Unknown emoji.
- Skin-tone modifiers on their own.
- Text and code with no emoji.

## Limits

- It never runs automatically.
- There is no reverse conversion from shortcode back to emoji.

## Pinned Dataset

- The map is generated from a pinned `iamcal/emoji-data` revision.

Pinned dataset: iamcal/emoji-data v16.0.0 (2771d0b1b3af25c069086e68e38f901c3dda8bdf)

## Help

- After installing, open the documentation with `:help emoji-to-text`.

## Development

### Checks

```bash
make generate-check
make test
make refresh-check
```

### Behavior Specs (`vim-themis`)

- *CI runs the behavior specs on the distribution's Vim and on Neovim v0.12.5.*

```bash
make test
```

### Both Suites In Parallel

```bash
make -j2 test
```

### Benchmarks

#### Informational Run

```bash
make bench
```

#### Baseline Gate

```bash
make bench-check
```

## Release Process

- See [`docs/RELEASING.md`](https://github.com/efournier92/vim-emoji-to-text/blob/main/docs/RELEASING.md).
- See [`CHANGELOG.md`](https://github.com/efournier92/vim-emoji-to-text/blob/main/CHANGELOG.md) for the release history.

## Contributing

- Issues and pull requests are welcome on the [GitHub repository](https://github.com/efournier92/vim-emoji-to-text).

## License

- MIT. See [`LICENSE`](https://github.com/efournier92/vim-emoji-to-text/blob/main/LICENSE) and [`NOTICE`](https://github.com/efournier92/vim-emoji-to-text/blob/main/NOTICE).

