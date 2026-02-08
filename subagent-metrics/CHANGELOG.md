## subagent-metrics-v0.1.1 (2026-02-08)

### Feat

- **commit**: add smart conventional commit plugin with Opus/Haiku architecture
- **marketplace**: add CLI script for managing plugin catalog
- **test-runner**: add test-runner plugin with custom subagent
- init cc-plugins marketplace

### Fix

- **test-runner**: pass compare script path via skill prompt
- **subagent-metrics**: extract token usage from tool_response JSON object
- **commit**: replace set -x with section headers and context-aware git log
- **commit**: add bullet point guidance for commit message bodies
- **commit**: use fully-qualified subagent_type in skill instructions
- **subagent-metrics**: read tool_response instead of tool_result, replace loaded_skills with cwd
- **mise**: use pipx backend for commitizen installation

### Refactor

- remove explicit interpreter prefixes from script invocations
- **commit**: extract git info-gathering into standalone script
