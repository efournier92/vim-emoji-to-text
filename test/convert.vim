" Behavior specs for EmojiToText (vim-themis, basic style).
" Covers Test Plan cases 1-22 from
" docs/specs/2026-10-05_EmojiToText.md. The seam is the :EmojiToText
" command end to end on a scratch buffer, run under Vim and Neovim.
scriptencoding utf-8

let s:suite = themis#suite('convert')
let s:assert = themis#helper('assert')

function! s:suite.before_each() abort
  silent! enew!
  setlocal buftype=nofile bufhidden=wipe noswapfile
  silent! %delete _
  call setline(1, [''])
endfunction

function! s:set_lines(lines) abort
  silent! %delete _
  call setline(1, a:lines)
endfunction

" 1. Single emoji.
function! s:suite.case_01_single_emoji() abort
  call s:set_lines(['😀'])
  EmojiToText
  call s:assert.equals(getline(1), ':grinning:')
endfunction

" 2. Multiple per line.
function! s:suite.case_02_multiple_per_line() abort
  call s:set_lines(['😀😀'])
  EmojiToText
  call s:assert.equals(getline(1), ':grinning::grinning:')
endfunction

" 3. Adjacent text.
function! s:suite.case_03_adjacent_text() abort
  call s:set_lines(['hi😀there'])
  EmojiToText
  call s:assert.equals(getline(1), 'hi:grinning:there')
endfunction

" 4. Multi-line buffer: every line is converted, not just the cursor line.
function! s:suite.case_04_multiline_buffer() abort
  call s:set_lines(['😀', '👋', 'plain'])
  call cursor(1, 1)
  EmojiToText
  call s:assert.equals(getline(1), ':grinning:')
  call s:assert.equals(getline(2), ':wave:')
  call s:assert.equals(getline(3), 'plain')
endfunction

" 5. Zero-width-joiner family: longest match wins.
function! s:suite.case_05_zwj_family() abort
  call s:set_lines(['👨‍👩‍👧'])
  EmojiToText
  call s:assert.equals(getline(1), ':man-woman-girl:')
endfunction

" 6. Couple sequence (ZWJ man-heart-man; spec literal U+1F491 was a
" rendering typo, expected value is the spec's :man-heart-man:).
function! s:suite.case_06_couple_sequence() abort
  call s:set_lines(['👨‍❤️‍👨'])
  EmojiToText
  call s:assert.equals(getline(1), ':man-heart-man:')
endfunction

" 7. Skin tone dropped.
function! s:suite.case_07_skin_tone_dropped() abort
  call s:set_lines(['👍🏻', '👋🏽'])
  EmojiToText
  call s:assert.equals(getline(1), ':+1:')
  call s:assert.equals(getline(2), ':wave:')
endfunction

" 8. Bare modifier left alone (Component entries are excluded).
function! s:suite.case_08_bare_modifier() abort
  call s:set_lines(['🏼'])
  EmojiToText
  call s:assert.equals(getline(1), '🏼')
endfunction

" 9. Country flag.
function! s:suite.case_09_country_flag() abort
  call s:set_lines(['🇺🇸', '🇨🇳'])
  EmojiToText
  call s:assert.equals(getline(1), ':flag-us:')
  call s:assert.equals(getline(2), ':flag-cn:')
endfunction

" 10. Keycap digit.
function! s:suite.case_10_keycap_digit() abort
  call s:set_lines(['1️⃣'])
  EmojiToText
  call s:assert.equals(getline(1), ':one:')
endfunction

" 11. Keycap asterisk, exercising metacharacter escaping.
function! s:suite.case_11_keycap_asterisk() abort
  call s:set_lines(['*️⃣'])
  EmojiToText
  call s:assert.equals(getline(1), ':keycap_star:')
endfunction

" 12. Keycap hash.
function! s:suite.case_12_keycap_hash() abort
  call s:set_lines(['#️⃣'])
  EmojiToText
  call s:assert.equals(getline(1), ':hash:')
endfunction

" 13. Variation selector.
function! s:suite.case_13_variation_selector() abort
  call s:set_lines(['❤️'])
  EmojiToText
  call s:assert.equals(getline(1), ':heart:')
endfunction

" 14. Non-qualified form untouched.
function! s:suite.case_14_non_qualified_untouched() abort
  call s:set_lines(['❤', '©'])
  EmojiToText
  call s:assert.equals(getline(1), '❤')
  call s:assert.equals(getline(2), '©')
endfunction

" 15. Unknown input untouched.
function! s:suite.case_15_unknown_untouched() abort
  call s:set_lines(['x' . nr2char(0x1FAEA) . 'y'])
  EmojiToText
  call s:assert.equals(getline(1), 'x' . nr2char(0x1FAEA) . 'y')
endfunction

" 16. Idempotency: a second run changes nothing.
function! s:suite.case_16_idempotency() abort
  call s:set_lines(['😀 and 👨‍👩‍👧'])
  EmojiToText
  let l:once = getline(1)
  EmojiToText
  call s:assert.equals(getline(1), l:once)
endfunction

" 17. Undo: one u restores the original buffer exactly. The original
" content is loaded from a file, so it is a committed undo state exactly
" as it is in a real session, with no artificial undo sync.
function! s:suite.case_17_undo_single_step() abort
  let l:original = '😀 and text'
  let l:file = tempname()
  call writefile([l:original], l:file)
  execute 'silent edit!' fnameescape(l:file)
  EmojiToText
  call s:assert.equals(getline(1), ':grinning: and text')
  silent undo
  call s:assert.equals(getline(1), l:original)
  call delete(l:file)
endfunction

" 18. No-op safety: a buffer with no emoji is unchanged, no error.
function! s:suite.case_18_noop_safety() abort
  call s:set_lines(['plain text only'])
  EmojiToText
  call s:assert.equals(getline(1), 'plain text only')
endfunction

" 19. Empty buffer: no error.
function! s:suite.case_19_empty_buffer() abort
  call s:set_lines([''])
  EmojiToText
  call s:assert.equals(getline(1), '')
endfunction

" 20. Search register preserved.
function! s:suite.case_20_search_register_preserved() abort
  call setreg('/', 'keepme')
  call s:set_lines(['😀'])
  EmojiToText
  call s:assert.equals(getreg('/'), 'keepme')
endfunction

" 21. Name containing plus.
function! s:suite.case_21_name_with_plus() abort
  call s:set_lines(['👍'])
  EmojiToText
  call s:assert.equals(getline(1), ':+1:')
endfunction

" 22. Data load: the generated map is a non-empty dictionary.
function! s:suite.case_22_data_load() abort
  let l:map = emoji_to_text#data#map()
  call s:assert.equals(type(l:map), type({}))
  call s:assert.not_empty(l:map)
endfunction

" Guard: the plugin sets its load flag and tolerates a double source.
function! s:suite.guard_double_load() abort
  let l:plugin = getcwd() . '/plugin/emoji_to_text.vim'
  execute 'source ' . fnameescape(l:plugin)
  execute 'source ' . fnameescape(l:plugin)
  call s:assert.equals(get(g:, 'loaded_emoji_to_text', 0), 1)
  call s:assert.equals(exists(':EmojiToText'), 2)
endfunction

" Direct API seam: emoji_to_text#convert() behaves like the command.
function! s:suite.api_convert_function() abort
  call s:set_lines(['😀'])
  call emoji_to_text#convert()
  call s:assert.equals(getline(1), ':grinning:')
endfunction
