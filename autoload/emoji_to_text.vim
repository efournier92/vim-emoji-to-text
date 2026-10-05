" EmojiToText conversion engine: whole-buffer emoji to :shortcode:.
scriptencoding utf-8

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
  " The emoji map is UTF-8; decline clearly instead of failing on load.
  if tolower(&encoding) !=# 'utf-8'
    echomsg 'EmojiToText: requires encoding=utf-8; buffer left unchanged'
    return
  endif
  if empty(s:map)
    let s:map = emoji_to_text#data#map()
    call s:build_pattern()
  endif
  let l:pos = getcurpos()
  silent! execute 'keeppatterns %s/' . s:pattern . '/\=s:replace_match(submatch(0))/ge'
  call setpos('.', l:pos)
endfunction
