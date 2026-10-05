" Benchmark emoji_to_text#convert() over representative buffers.
" Invoke via bench/run.sh; writes results to $BENCH_OUT.
scriptencoding utf-8

let s:root = expand('<sfile>:p:h:h')
execute 'set runtimepath^=' . fnameescape(s:root)

let s:out = []
if empty($BENCH_OUT)
  let $BENCH_OUT = '/tmp/et_bench_exec.txt'
endif
let s:ascii = 'the quick brown fox jumps over the lazy dog 0123456789'
let s:light = 'line text 😀 more text'
let s:heavy = '😀👨‍👩‍👧👍🏻🇺🇸1️⃣❤️text'

function! s:payload(kind, lines) abort
  if a:kind ==# 'empty'
    return ['']
  elseif a:kind ==# 'ascii'
    return repeat([s:ascii], a:lines)
  elseif a:kind ==# 'light'
    return repeat([s:light], a:lines)
  elseif a:kind ==# 'heavy'
    return repeat([s:heavy], a:lines)
  elseif a:kind ==# 'mixed'
    let l:rows = []
    for l:i in range(a:lines)
      call add(l:rows, l:i % 20 == 0 ? s:heavy : s:ascii)
    endfor
    return l:rows
  endif
  throw 'unknown payload: ' . a:kind
endfunction

function! s:bench(kind, lines, reps) abort
  let l:rows = s:payload(a:kind, a:lines)
  silent! enew!
  setlocal buftype=nofile bufhidden=wipe noswapfile
  " Warm run loads the map and builds the cached pattern.
  call setline(1, l:rows)
  call emoji_to_text#convert()
  let l:total = 0.0
  for l:i in range(a:reps)
    call setline(1, l:rows)
    let l:t = reltime()
    call emoji_to_text#convert()
    let l:total += reltimefloat(reltime(l:t))
  endfor
  call add(s:out, printf('exec %s lines=%d reps=%d per_run_ms=%.3f',
        \ a:kind, a:lines, a:reps, l:total * 1000.0 / a:reps))
  call writefile(s:out, $BENCH_OUT)
endfunction

call writefile(['started'], $BENCH_OUT)
try
  call s:bench('empty', 1, 20)
  call s:bench('ascii', 200, 3)
  call s:bench('mixed', 200, 3)
  call s:bench('light', 200, 3)
  call s:bench('heavy', 200, 3)
  call s:bench('heavy', 1000, 1)
catch
  call add(s:out, 'exec ERROR ' . v:exception)
endtry

call writefile(s:out, $BENCH_OUT)
qa!
