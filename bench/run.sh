#!/usr/bin/env bash
# Unified performance harness for EmojiToText.
#   bench/run.sh [exec|load|install|build|all]
# Reports one metric per line as "<dimension> <key>=<value> ...".
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIM="${1:-all}"
OUT="${BENCH_OUT:-/tmp/et_bench.txt}"
: > "$OUT"

run_exec() {
  local editor="$1" bin="$2" args="$3"
  local tmp="/tmp/et_bench_exec_${editor}.txt"
  BENCH_OUT="$tmp" $bin -Nu NONE $args -S "$ROOT/bench/bench_exec.vim" >/dev/null 2>&1
  while IFS= read -r line; do
    echo "${line/exec /exec editor=$editor }" >> "$OUT"
  done < "$tmp"
}

run_load() {
  local editor="$1" bin="$2" args="$3"
  local st="/tmp/et_start_${editor}.txt"
  local st2="/tmp/et_start_${editor}_plugin.txt"
  $bin -Nu NONE $args --cmd 'set loadplugins' --startuptime "$st" -c 'qall' >/dev/null 2>&1
  $bin -Nu NONE $args --cmd 'set loadplugins' --cmd "set runtimepath^=$ROOT" --startuptime "$st2" -c 'qall' >/dev/null 2>&1
  local base plugin
  base=$(awk '{v=$1+0; if(v>m)m=v} END{print m+0}' "$st")
  plugin=$(awk '{v=$1+0; if(v>m)m=v} END{print m+0}' "$st2")
  echo "load editor=$editor base_ms=$base plugin_ms=$plugin delta_ms=$(awk "BEGIN{printf \"%.3f\", $plugin-$base}")" >> "$OUT"
}

run_install() {
  local bytes files
  bytes=$(git -C "$ROOT" archive --format=tar.gz HEAD | wc -c | tr -d ' ')
  files=$(git -C "$ROOT" ls-files | wc -l | tr -d ' ')
  echo "install archive_bytes=$bytes files=$files" >> "$OUT"
}

run_build() {
  local t0 t1
  t0=$(date +%s.%N)
  make -C "$ROOT" generate-check >/dev/null 2>&1
  t1=$(date +%s.%N)
  echo "build generate_check_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
  t0=$(date +%s.%N)
  make -C "$ROOT" test-vim >/dev/null 2>&1
  t1=$(date +%s.%N)
  echo "build test_vim_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
  t0=$(date +%s.%N)
  make -C "$ROOT" test-nvim >/dev/null 2>&1
  t1=$(date +%s.%N)
  echo "build test_nvim_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
}

case "$DIM" in
  exec)    run_exec vim vim "-e -s"; run_exec nvim nvim "-e --headless" ;;
  load)    run_load vim vim "-e -s"; run_load nvim nvim "-e --headless" ;;
  install) run_install ;;
  build)   run_build ;;
  all)
    run_exec vim vim "-e -s"; run_exec nvim nvim "-e --headless"
    run_load vim vim "-e -s"; run_load nvim nvim "-e --headless"
    run_install; run_build
    ;;
  *) echo "usage: bench/run.sh [exec|load|install|build|all]" >&2; exit 2 ;;
esac

cat "$OUT"
