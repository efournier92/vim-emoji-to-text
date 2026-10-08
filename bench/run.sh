#!/usr/bin/env bash
# Unified performance harness for EmojiToText.
#   bench/run.sh [exec|load|install|build|all] ...
# Reports one metric per line as "<dimension> <key>=<value> ...".
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${BENCH_OUT:-/tmp/et_bench.txt}"
: > "$OUT"

VIM_BIN="${VIM_BIN:-vim}"
NVIM_BIN="${NVIM_BIN:-nvim}"

# Portable wall-clock; python3 is already a hard prerequisite of the harness.
now() {
  python3 -c 'import time; print("%.6f" % time.time())'
}

TMP_FILES=()
cleanup() {
  if [ "${#TMP_FILES[@]}" -gt 0 ]; then
    rm -f "${TMP_FILES[@]}"
  fi
}
trap cleanup EXIT

# Scratch files are per-run; call as `scratch <name>`, read the path from $SCRATCH.
SCRATCH=""
scratch() {
  SCRATCH=$(mktemp "${TMPDIR:-/tmp}/et_bench_$1.XXXXXX")
  TMP_FILES+=("$SCRATCH")
}

require_bin() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "bench/run.sh: required editor binary not found: $1" >&2
    exit 2
  fi
}

run_exec() {
  local editor="$1" bin="$2" args="$3"
  require_bin "$bin"
  scratch "exec_${editor}"
  local tmp="$SCRATCH"
  BENCH_OUT="$tmp" $bin -Nu NONE $args -S "$ROOT/bench/bench_exec.vim" >/dev/null 2>&1
  while IFS= read -r line; do
    case "$line" in
      *editor=*) echo "$line" >> "$OUT" ;;
      *) echo "${line/ / editor=$editor }" >> "$OUT" ;;
    esac
  done < "$tmp"
}

run_load() {
  local editor="$1" bin="$2" args="$3"
  require_bin "$bin"
  local st st2
  scratch "start_${editor}"; st="$SCRATCH"
  scratch "start_${editor}_plugin"; st2="$SCRATCH"
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
  t0=$(now)
  make -C "$ROOT" generate-check >/dev/null 2>&1
  t1=$(now)
  echo "build generate_check_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
  t0=$(now)
  make -C "$ROOT" test-vim >/dev/null 2>&1
  t1=$(now)
  echo "build test_vim_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
  t0=$(now)
  make -C "$ROOT" test-nvim >/dev/null 2>&1
  t1=$(now)
  echo "build test_nvim_s=$(awk "BEGIN{printf \"%.3f\", $t1-$t0}")" >> "$OUT"
}

dims=("$@")
if [ "${#dims[@]}" -eq 0 ]; then
  dims=(all)
fi

for dim in "${dims[@]}"; do
  case "$dim" in
    exec)
      run_exec vim "$VIM_BIN" "-e -s"; run_exec nvim "$NVIM_BIN" "-e --headless"
      ;;
    load)
      run_load vim "$VIM_BIN" "-e -s"; run_load nvim "$NVIM_BIN" "-e --headless"
      ;;
    install) run_install ;;
    build)   run_build ;;
    all)
      run_exec vim "$VIM_BIN" "-e -s"; run_exec nvim "$NVIM_BIN" "-e --headless"
      run_load vim "$VIM_BIN" "-e -s"; run_load nvim "$NVIM_BIN" "-e --headless"
      run_install; run_build
      ;;
    *) echo "usage: bench/run.sh [exec|load|install|build|all] ..." >&2; exit 2 ;;
  esac
done

cat "$OUT"
