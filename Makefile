.PHONY: help install reinstall uninstall upgrade dev build clean test completions

PKG := gitlab-cli-explorer

help:
	@echo "gitlab-cli (gl) - make targets"
	@echo ""
	@echo "  make install       pipx install -e . (editable, global)"
	@echo "  make reinstall     pipx uninstall + install -e ."
	@echo "  make upgrade       pipx upgrade $(PKG)"
	@echo "  make uninstall     pipx uninstall $(PKG)"
	@echo "  make dev           pip install -e . (for venv dev)"
	@echo "  make build         python -m build (sdist + wheel)"
	@echo "  make test          run manual test scripts"
	@echo "  make completions   install shell completions (bash/zsh)"
	@echo "  make clean         remove build artifacts"

install:
	pipx install -e . --force

reinstall:
	-pipx uninstall $(PKG)
	pipx install -e . --force

upgrade:
	pipx upgrade $(PKG)

uninstall:
	pipx uninstall $(PKG)

dev:
	pip install -e .

build:
	python -m build

test:
	python test_cli_v3.py
	python test_cache.py
	python test_git_detection.py
	python test_stage_url.py

completions:
	./completion/install.sh

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
