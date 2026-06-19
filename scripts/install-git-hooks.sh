#!/bin/bash
# Install repository git hooks.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_HOOKS_DIR="$(git rev-parse --git-dir)/hooks"

echo "Installing git hooks..."

install -m 0755 "$SCRIPT_DIR/git-hooks/pre-commit" "$GIT_HOOKS_DIR/pre-commit"

echo "Installed pre-commit hook"
