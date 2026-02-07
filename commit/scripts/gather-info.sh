#!/usr/bin/env bash
set -euo pipefail
set -x

cd "$(git rev-parse --show-toplevel)"

git status
git diff
git diff --staged
git log --oneline -5
