#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

chmod +x "$repo_root/.githooks/pre-commit"
git config core.hooksPath .githooks

echo "Git hooks configured: core.hooksPath=.githooks"
echo "pre-commit will now run frontend and backend lint checks."
