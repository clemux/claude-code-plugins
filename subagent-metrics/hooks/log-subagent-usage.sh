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

# Extract token usage from tool_result (text format)
tool_result="$(echo "$input" | jq -r '.tool_result // ""')"

total_tokens="null"
if [[ "$tool_result" =~ total_tokens:\ *([0-9]+) ]]; then
  total_tokens="${BASH_REMATCH[1]}"
fi

duration_ms="null"
if [[ "$tool_result" =~ duration_ms:\ *([0-9]+) ]]; then
  duration_ms="${BASH_REMATCH[1]}"
fi

# List loaded skills by globbing SKILL.md files
loaded_skills="[]"
skill_files=()
for f in "$HOME"/.claude/skills/*/SKILL.md; do
  if [[ -f "$f" ]]; then
    # Extract skill name from path
    dir="$(dirname "$f")"
    name="$(basename "$dir")"
    skill_files+=("\"$name\"")
  fi
done
if [[ ${#skill_files[@]} -gt 0 ]]; then
  loaded_skills="[$(IFS=,; echo "${skill_files[*]}")]"
fi

# Build JSON log line
ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

log_line="$(jq -n -c \
  --arg ts "$ts" \
  --arg session "$session_id" \
  --arg model "$model" \
  --arg subagent_type "$subagent_type" \
  --argjson skill "$skill" \
  --arg description "$description" \
  --argjson total_tokens "$total_tokens" \
  --argjson duration_ms "$duration_ms" \
  --argjson loaded_skills "$loaded_skills" \
  '{ts:$ts,session:$session,model:$model,subagent_type:$subagent_type,skill:$skill,description:$description,total_tokens:$total_tokens,duration_ms:$duration_ms,loaded_skills:$loaded_skills}'
)"

# Atomic append using flock to prevent race conditions from concurrent subagents
log_file="$HOME/.claude/subagent-metrics.jsonl"
(
  flock -x 200
  echo "$log_line" >> "$log_file"
) 200>"${log_file}.lock"

# Non-blocking: exit 0, no transcript output
exit 0
