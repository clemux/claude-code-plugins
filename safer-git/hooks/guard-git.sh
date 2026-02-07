#!/usr/bin/env bash
set -euo pipefail

# Check jq dependency
if ! command -v jq &>/dev/null; then
  echo '{"permissionDecision":"deny","systemMessage":"safer-git: jq is required but not found. Install jq to use this plugin."}' >&2
  exit 2
fi

# Read hook input from stdin
input="$(cat)"

# Extract the command from tool_input
command_str="$(echo "$input" | jq -r '.tool_input.command // empty')"

# If no command found, allow
if [[ -z "$command_str" ]]; then
  exit 0
fi

# Blocked patterns: regex => human-readable description
# Each pattern matches the dangerous flag anywhere after the git subcommand
declare -a PATTERNS=(
  # Force push variants (history rewrite on remote)
  'git\s+push\s+.*(-f|--force)'
  'git\s+push\s+.*--force-with-lease'
  'git\s+push\s+.*--delete'
  'git\s+push\s+[^-]*:[^\s]'
  # Commit history rewrite / hook bypass
  'git\s+commit\s+.*--amend'
  'git\s+commit\s+.*(--no-verify|-n\b)'
  # Discard uncommitted work
  'git\s+reset\s+.*--hard'
  'git\s+checkout\s+\.\s*$'
  'git\s+restore\s+\.\s*$'
  'git\s+clean\s+.*-f'
  # Branch destruction
  'git\s+branch\s+.*-D'
  # History rewrite tools
  'git\s+rebase\s+.*(-i|--interactive)'
  'git\s+filter-branch'
  # Stash destruction (irrecoverable)
  'git\s+stash\s+drop'
  'git\s+stash\s+clear'
  # Safety net destruction
  'git\s+reflog\s+expire'
  'git\s+gc\s+.*--prune'
  # Alias creation (bypass vector: git config alias.yolo "push --force")
  'git\s+config\s+.*alias\.'
)

declare -a DESCRIPTIONS=(
  "Force push (rewrites remote history)"
  "Force push with lease (still rewrites remote history)"
  "Delete remote branch via push --delete"
  "Delete remote branch via colon-refspec push"
  "Amend commit (rewrites history)"
  "Skip pre-commit hooks (--no-verify)"
  "Hard reset (discards uncommitted changes)"
  "Checkout . (discards all working tree changes)"
  "Restore . (discards all working tree changes)"
  "Clean with -f (deletes untracked files)"
  "Force-delete branch (-D)"
  "Interactive rebase (history rewrite)"
  "filter-branch (full history rewrite)"
  "Stash drop (permanently deletes stash entry)"
  "Stash clear (permanently deletes all stashes)"
  "Reflog expire (removes recovery safety net)"
  "GC prune (makes unreachable objects unrecoverable)"
  "Git alias creation (can bypass safety checks)"
)

# Split compound commands on &&, ||, ;, | and check each segment
# Use sed to normalize separators, then iterate
check_segment() {
  local segment="$1"
  # Trim leading/trailing whitespace
  segment="$(echo "$segment" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

  # Skip empty segments
  if [[ -z "$segment" ]]; then
    return 0
  fi

  for i in "${!PATTERNS[@]}"; do
    if echo "$segment" | grep -qP "${PATTERNS[$i]}"; then
      local msg="safer-git: BLOCKED — ${DESCRIPTIONS[$i]}. Command: $segment"
      echo "{\"permissionDecision\":\"deny\",\"systemMessage\":\"$msg\"}" >&2
      exit 2
    fi
  done
}

# Split on &&, ||, ;, | (but not ||'s second pipe, handle carefully)
# Replace compound operators with a unique delimiter, then split
segments="$(echo "$command_str" | sed 's/&&/\n/g; s/||/\n/g; s/;/\n/g; s/|/\n/g')"

while IFS= read -r segment; do
  check_segment "$segment"
done <<< "$segments"

# Command is safe
exit 0
