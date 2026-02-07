#!/usr/bin/env bash
set -euo pipefail

# Check jq dependency
if ! command -v jq &>/dev/null; then
  # Non-blocking: just exit silently if jq is missing
  exit 0
fi

# Read hook input from stdin
input="$(cat)"

# Extract fields from tool_input
model="$(echo "$input" | jq -r '.tool_input.model // "default"')"
subagent_type="$(echo "$input" | jq -r '.tool_input.subagent_type // "unknown"')"
description="$(echo "$input" | jq -r '.tool_input.description // ""')"
session_id="$(echo "$input" | jq -r '.session_id // ""')"

# Extract triggering skill from description tag convention: "[skill-name] ..."
skill="null"
if [[ "$description" =~ ^\[([^]]+)\] ]]; then
  skill="\"${BASH_REMATCH[1]}\""
fi

# Extract project path from hook event
cwd="$(echo "$input" | jq -r '.cwd // ""')"

# Extract token usage from tool_response (JSON object)
total_tokens="$(echo "$input" | jq '.tool_response.totalTokens // null')"
duration_ms="$(echo "$input" | jq '.tool_response.totalDurationMs // null')"

# Build JSON log line
ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

log_line="$(jq -n -c \
  --arg ts "$ts" \
  --arg session "$session_id" \
  --arg cwd "$cwd" \
  --arg model "$model" \
  --arg subagent_type "$subagent_type" \
  --argjson skill "$skill" \
  --arg description "$description" \
  --argjson total_tokens "$total_tokens" \
  --argjson duration_ms "$duration_ms" \
  '{ts:$ts,session:$session,cwd:$cwd,model:$model,subagent_type:$subagent_type,skill:$skill,description:$description,total_tokens:$total_tokens,duration_ms:$duration_ms}'
)"

# Atomic append using flock to prevent race conditions from concurrent subagents
log_file="$HOME/.claude/subagent-metrics.jsonl"
(
  flock -x 200
  echo "$log_line" >> "$log_file"
) 200>"${log_file}.lock"

# Non-blocking: exit 0, no transcript output
exit 0
