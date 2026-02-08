#!/usr/bin/env bash
set -euo pipefail

input=$(cat)

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')
model=$(printf '%s' "$input" | jq -r '.model // empty')

if [[ -z "$session_id" || -z "$model" ]]; then
  exit 0
fi

state_dir="${XDG_RUNTIME_DIR:-/tmp}/plan-guard"
mkdir -p "$state_dir"
printf '%s' "$model" > "${state_dir}/model-${session_id}"

exit 0
