## commit-v0.1.3 (2026-02-08)

### Fix

- **commit**: replace set -x with section headers and context-aware git log

### Refactor

- remove explicit interpreter prefixes from script invocations
- **commit**: extract git info-gathering into standalone script

## commit-v0.1.2 (2026-02-07)

### Fix

- **commit**: add bullet point guidance for commit message bodies

## commit-v0.1.1 (2026-02-07)

### Feat

- **commit**: add smart conventional commit plugin with Opus/Haiku architecture
- **marketplace**: add CLI script for managing plugin catalog
- **test-runner**: add test-runner plugin with custom subagent
- init cc-plugins marketplace

### Fix

- **commit**: use fully-qualified subagent_type in skill instructions
- **subagent-metrics**: read tool_response instead of tool_result, replace loaded_skills with cwd
- **mise**: use pipx backend for commitizen installation
