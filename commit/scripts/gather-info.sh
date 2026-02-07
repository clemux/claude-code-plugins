#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "=== git status ==="
git status

echo "=== git diff ==="
git diff

echo "=== git diff --staged ==="
git diff --staged

echo "=== git log ==="

# Detect default branch
default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@') || true
if [ -z "$default_branch" ]; then
  if git rev-parse --verify main >/dev/null 2>&1; then
    default_branch="main"
  elif git rev-parse --verify master >/dev/null 2>&1; then
    default_branch="master"
  fi
fi

current_branch=$(git branch --show-current)

log_output=""
if [ -n "$current_branch" ] && [ -n "$default_branch" ]; then
  if [ "$current_branch" = "$default_branch" ]; then
    # On default branch — show unpushed commits
    if git rev-parse --verify "origin/${default_branch}" >/dev/null 2>&1; then
      log_output=$(git log --oneline "origin/${default_branch}..${default_branch}")
    fi
  else
    # On feature branch — show branch-specific commits
    log_output=$(git log --oneline "${default_branch}..HEAD")
  fi
fi

if [ -n "$log_output" ]; then
  echo "$log_output"
else
  # Fallback: show last 5 commits for style context
  git log --oneline -5
fi
