# EmojiToText

A Vim 8+ and Neovim plugin that replaces fully-qualified emoji in the current buffer with Slack-style `:shortcode:` text, for example `:grinning:`.

Works in Vim 8.0+ and Neovim from one pure-Vimscript codebase with no runtime dependencies.

## Install

EmojiToText is a standard runtimepath plugin: no build step, no runtime dependencies, and no editor-specific files. It works with any Vim or Neovim plugin manager, including vim-plug, Vundle, Pathogen, dein.vim, minpac, lazy.nvim, packer.nvim, and Vim's native `packages` (`:packadd`), or a manual `set runtimepath+=/path/to/vim-emoji-to-text`.

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

Run the checks with `make generate-check`, `make test`, and `make refresh-check`. `make test` runs the vim-themis behavior specs under both Vim and Neovim.

## License

MIT. See `LICENSE` and `NOTICE`.
