set shell := ["bash", "-cu"]

MARKDOWNLINT_IMAGE := "ghcr.io/igorshubovych/markdownlint-cli:latest"
BLUE := '\033[0;34m'
RESET := '\033[0m'

# Codex sandboxes can make uv's default cache read-only. Claude Code and manual
# local runs work with the normal cache, so only use the fallback when needed or
# if UV_CACHE_DIR is already set by the caller.
UV_CACHE := "if [[ -z \"${UV_CACHE_DIR:-}\" && ! -w \"${XDG_CACHE_HOME:-$HOME/.cache}/uv\" ]]; then export UV_CACHE_DIR=/home/nevd/.tmp/uv-cache; fi"

# Show help.
@_:
    just --list

# Install git hooks.
install_hooks:
    ln -sf ../../scripts/pre-push .git/hooks/pre-push

# Serve locally and open in browser.
serve:
    scripts/local_serve.py

# Format Markdown files.
format:
    @echo $'{{ BLUE }}Formatting Markdown files...{{ RESET }}'
    uv tool run --with mdformat-gfm --with mdformat-frontmatter mdformat --number .claude/ docs/ design_docs/ README.md

# Lint Markdown files.
lint: format
    @echo $'{{ BLUE }}Linting Markdown files...{{ RESET }}'
    docker pull {{ MARKDOWNLINT_IMAGE }} > /dev/null
    docker run --pull always --rm -u "$(id -u):$(id -g)" -v "$(pwd)":/workdir {{ MARKDOWNLINT_IMAGE }} /workdir/.claude /workdir/docs /workdir/design_docs /workdir/README.md

# Run tests.
test:
    node test.js
    {{ UV_CACHE }}; uv run scripts/test_compact_jmdict.py

# Download source if needed and generate JMdict lookup files.
build-dict:
    {{ UV_CACHE }}; uv run scripts/download_jmdict_source.py
    {{ UV_CACHE }}; uv run scripts/compact_jmdict.py

# Tag the release and push.
tag_and_push: lint
    scripts/tag_and_push.sh
