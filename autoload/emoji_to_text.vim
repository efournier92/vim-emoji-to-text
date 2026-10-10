" EmojiToText conversion engine: emoji to :shortcode: over an optional range.
scriptencoding utf-8

let s:map = {}
let s:trie = {}

" Build a character trie over the UTF-8 keys once. Walking one character per
" dict lookup is O(line length) and avoids recompiling a 3781-alternative
" regex per call; split() keeps base+combining marks as one token on both sides.
function! s:build_trie() abort
  let s:trie = {}
  for l:key in keys(s:map)
    let l:node = s:trie
    for l:tok in split(l:key, '\zs')
      if !has_key(l:node, l:tok)
        let l:node[l:tok] = {}
      endif
      let l:node = l:node[l:tok]
    endfor
    let l:node[''] = s:map[l:key]
  endfor
endfunction

" Replace emoji in one line by walking the trie; deepest terminal wins.
function! s:convert_line(line) abort
  let l:toks = split(a:line, '\zs')
  let l:len = len(l:toks)
  let l:parts = []
  let l:last = 0
  let l:i = 0
  while l:i < l:len
    " Non-start characters (ASCII, stray combining marks) skip the walk.
    let l:node = get(s:trie, l:toks[l:i], 0)
    if l:node is 0
      let l:i += 1
      continue
    endif
    let l:best = get(l:node, '', '')
    let l:bestend = l:i + 1
    let l:j = l:i + 1
    while l:j < l:len
      let l:child = get(l:node, l:toks[l:j], 0)
      if l:child is 0
        break
      endif
      let l:node = l:child
      let l:j += 1
      if has_key(l:node, '')
        let l:best = l:node['']
        let l:bestend = l:j
      endif
    endwhile
    if empty(l:best)
      let l:i += 1
    else
      if l:last < l:i
        call add(l:parts, join(l:toks[l:last : l:i-1], ''))
      endif
      " No separator between consecutive emoji: Slack parses :a::b: as two
      " shortcodes (a close colon plus an open colon), and a space would
      " inject bytes the buffer never held.
      call add(l:parts, ':' . l:best . ':')
      let l:i = l:bestend
      let l:last = l:i
    endif
  endwhile
  if empty(l:parts)
    return a:line
  endif
  if l:last < l:len
    call add(l:parts, join(l:toks[l:last :], ''))
  endif
  return join(l:parts, '')
endfunction

function! emoji_to_text#convert(...) abort
  " The emoji map is UTF-8; decline clearly instead of failing on load.
  if tolower(&encoding) !=# 'utf-8'
    echomsg 'EmojiToText: requires encoding=utf-8; buffer left unchanged'
    return
  endif
  if !&modifiable
    echomsg 'EmojiToText: buffer is not modifiable; buffer left unchanged'
    return
  endif
  if empty(s:map)
    let s:map = emoji_to_text#data#map()
    call s:build_trie()
  endif
  let l:start = a:0 >= 1 ? a:1 : 1
  let l:end = a:0 >= 2 ? a:2 : line('$')
  " Clamp into the buffer; an empty buffer is the single empty line 1.
  let l:start = max([1, min([l:start, line('$')])])
  let l:end = max([1, min([l:end, line('$')])])
  let l:pos = getcurpos()
  let l:lines = getline(l:start, l:end)
  let l:changed = 0
  let l:i = 0
  let l:n = len(l:lines)
  while l:i < l:n
    let l:line = l:lines[l:i]
    " Every key has a non-ASCII byte, so all-ASCII lines cannot match.
    if strlen(l:line) != strchars(l:line)
      let l:new = s:convert_line(l:line)
      if l:new !=# l:line
        let l:lines[l:i] = l:new
        let l:changed = 1
      endif
    endif
    let l:i += 1
  endwhile
  if l:changed
    " One setline over the slice keeps the range write a single undo step.
    call setline(l:start, l:lines)
  endif
  call setpos('.', l:pos)
endfunction
