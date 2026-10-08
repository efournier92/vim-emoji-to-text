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

" Pure-Vimscript CPU workload; the result is returned so it cannot be folded away.
function! s:calib(n) abort
  let l:acc = 0
  for l:i in range(a:n)
    let l:acc = (l:acc + l:i * 3) % 2147483647
  endfor
  return l:acc
endfunction

function! s:bench_calib(iterations, reps) abort
  call s:calib(a:iterations)
  let l:total = 0.0
  for l:i in range(a:reps)
    let l:t = reltime()
    call s:calib(a:iterations)
    let l:total += reltimefloat(reltime(l:t))
  endfor
  call add(s:out, printf('exec calib lines=%d reps=%d per_run_ms=%.3f',
        \ a:iterations, a:reps, l:total * 1000.0 / a:reps))
  call writefile(s:out, $BENCH_OUT)
endfunction

function! s:bench_source(reps) abort
  let l:path = s:root . '/autoload/emoji_to_text/data.vim'
  let l:times = []
  for l:i in range(a:reps)
    let l:t = reltime()
    execute 'source ' . fnameescape(l:path)
    call add(l:times, reltimefloat(reltime(l:t)) * 1000.0)
  endfor
  call sort(l:times)
  call add(s:out, printf('load source_data_ms=%.3f', l:times[len(l:times) / 2]))
  call writefile(s:out, $BENCH_OUT)
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
  call s:bench_calib(20000, 10)
  call s:bench('empty', 1, 100)
  call s:bench('ascii', 200, 10)
  call s:bench('mixed', 200, 10)
  call s:bench('light', 200, 10)
  call s:bench('heavy', 200, 10)
  call s:bench('heavy', 1000, 3)
  call s:bench_source(9)
catch
  call add(s:out, 'exec ERROR ' . v:exception)
endtry

call writefile(s:out, $BENCH_OUT)
qa!
