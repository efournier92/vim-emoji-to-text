# EmojiToText plugin Makefile
THEMIS_DIR ?= vendor/vim-themis
THEMIS_BIN := $(THEMIS_DIR)/bin/themis
PYTHON ?= python3

.PHONY: all generate generate-check refresh-map refresh-check test test-vim test-nvim release bench bench-record bench-check check-changelog check

all: generate-check test

generate:
	$(PYTHON) tools/generate_map.py

generate-check:
	$(PYTHON) tools/generate_map.py --check

refresh-map:
	$(PYTHON) tools/refresh_map.py

refresh-check:
	$(PYTHON) tools/refresh_map.py --dry-run

test: test-vim test-nvim

test-vim: $(THEMIS_BIN)
	THEMIS_VIM=vim THEMIS_ARGS="-e -s" $(THEMIS_BIN) test/

test-nvim: $(THEMIS_BIN)
	THEMIS_VIM=nvim THEMIS_ARGS="-e --headless" $(THEMIS_BIN) test/

$(THEMIS_BIN):
	git clone --branch v1.7.0 --depth 1 https://github.com/thinca/vim-themis.git $(THEMIS_DIR)

bench:
	BENCH_OUT=bench/last.txt bash bench/run.sh all

bench-record:
	@if [ "$$BENCH_RECORD_FORCE" != "1" ]; then echo "Refusing to overwrite bench/baseline.json; run the Bench Baseline workflow or set BENCH_RECORD_FORCE=1." >&2; exit 1; fi
	$(MAKE) bench
	$(PYTHON) bench/check.py --record --input bench/last.txt --output bench/baseline.json

bench-check: bench
	$(PYTHON) bench/check.py --check --input bench/last.txt --baseline bench/baseline.json

check-changelog:
	@if [ -z "$(DATE)" ]; then echo "DATE is unset" >&2; exit 1; fi
	$(PYTHON) tools/check_changelog.py $(DATE)

check: check-changelog

# Bare prerequisite so the documented `release: check DATE` invocation is valid.
DATE:

release: check DATE
	$(PYTHON) tools/refresh_map.py
	$(MAKE) test
	$(MAKE) generate-check
	git add tools/generate_map.py autoload/emoji_to_text/data.vim README.md NOTICE CHANGELOG.md
	@if git diff --cached --quiet; then \
		echo "EmojiToText release: pin already current, nothing to commit."; \
	else \
		git commit -m "Release $(DATE)"; \
	fi
