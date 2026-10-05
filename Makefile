# EmojiToText plugin Makefile
THEMIS_DIR ?= vendor/vim-themis
THEMIS_BIN := $(THEMIS_DIR)/bin/themis
PYTHON ?= python3

.PHONY: all generate generate-check refresh-map refresh-check test test-vim test-nvim release

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

release:
	$(PYTHON) tools/refresh_map.py
	$(MAKE) test
	$(MAKE) generate-check
	git add tools/generate_map.py autoload/emoji_to_text/data.vim README.md
	@if git diff --cached --quiet; then \
		echo "EmojiToText release: pin already current, nothing to commit."; \
	else \
		git commit -m "Refresh EmojiToText Dataset Pin"; \
	fi
