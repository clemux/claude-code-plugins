#!/usr/bin/env bash
set -euo pipefail

input=$(cat)

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')

if [[ -z "$session_id" ]]; then
  exit 0
fi

state_dir="${XDG_RUNTIME_DIR:-/tmp}/plan-guard"
rm -f "${state_dir}/model-${session_id}"

exit 0
