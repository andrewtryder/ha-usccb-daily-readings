#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -n $(git ls-files --others --exclude-standard) ]]; then
    echo "Error: move or commit untracked files before validation" >&2
    exit 1
fi

snapshot_dir=$(mktemp -d)
snapshot() {
    git status --porcelain=v1 --untracked-files=all > "$1/status"
    git diff --binary > "$1/worktree"
    git diff --cached --binary > "$1/index"
}
mkdir "$snapshot_dir/before" "$snapshot_dir/after"
snapshot "$snapshot_dir/before"
check_changes() {
    snapshot "$snapshot_dir/after"
    if ! diff -qr "$snapshot_dir/before" "$snapshot_dir/after" >/dev/null; then
        echo "Error: validation changed the working tree or index:" >&2
        git status --short >&2
        return 1
    fi
}
finish() {
    local result=$?
    check_changes || result=1
    rm -rf "$snapshot_dir"
    return "$result"
}
trap finish EXIT

echo "==> [1/5] Toolchain and lockfile"
command -v uv >/dev/null 2>&1 || { echo "Error: uv is required"; exit 1; }
uv sync --locked
uv run --locked python -c 'import sys; assert sys.version_info >= (3, 14, 2); print(sys.version)'
uv lock --check

echo "==> [2/5] pre-commit"
uv run --locked pre-commit run --all-files

echo "==> [3/5] Ruff"
uv run --locked ruff check .
uv run --locked ruff format --check .

echo "==> [4/5] Pytest (>=90% coverage, offline)"
uv run --locked pytest --disable-socket --allow-unix-socket -p no:cacheprovider

echo "==> [5/5] Working tree unchanged"
check_changes

echo "==> Local validation passed"
