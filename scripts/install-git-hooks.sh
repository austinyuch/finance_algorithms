#!/bin/bash
# Install repository git hooks.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR/.." rev-parse --show-toplevel)"
HOOKS_PATH="$(git -C "$REPO_ROOT" config --get core.hooksPath || true)"
if [ -n "$HOOKS_PATH" ]; then
    case "$HOOKS_PATH" in
        /*) GIT_HOOKS_DIR="$HOOKS_PATH" ;;
        *) GIT_HOOKS_DIR="$REPO_ROOT/$HOOKS_PATH" ;;
    esac
else
    GIT_HOOKS_DIR="$(git -C "$REPO_ROOT" rev-parse --git-dir)/hooks"
fi

echo "Installing git hooks..."

mkdir -p "$GIT_HOOKS_DIR"
install -m 0755 "$SCRIPT_DIR/git-hooks/pre-commit" "$GIT_HOOKS_DIR/pre-commit"

echo "Installed pre-commit hook"
