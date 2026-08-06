#!/bin/bash
#
# Stop Check Hook - Runs when Claude session ends
# Warns about uncommitted changes, open PRs, and other issues.
#
# Surfaced via JSON {"systemMessage": "..."} on stdout (exit 0), which
# Claude Code shows to the user without blocking the stop. A prior version
# wrote these warnings to stderr on exit 0 — per the Stop hook docs, stderr
# on exit 0 goes only to the debug log, never the transcript, so none of
# these warnings ever actually reached anyone. See
# https://code.claude.com/docs/en/hooks for the Stop hook output contract.
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$PROJECT_DIR"

WARNINGS=()

# Check uncommitted changes
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  WARNINGS+=("Uncommitted changes exist")
fi

# Check for open PR on current branch
PR_STATE=$(gh pr view --json state -q '.state' 2>/dev/null || echo "NONE")
if [ "$PR_STATE" = "OPEN" ]; then
  PR_NUM=$(gh pr view --json number -q '.number' 2>/dev/null)
  WARNINGS+=("PR #$PR_NUM is still OPEN - complete merge workflow?")
fi

# Check if on main branch with changes
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    WARNINGS+=("ON MAIN BRANCH with uncommitted changes - create feature branch!")
  fi
fi

# Emit a non-blocking systemMessage if there's anything to say. Building the
# JSON with python3 (already a hard dependency of this plugin) sidesteps
# manual quote/newline escaping.
if [ ${#WARNINGS[@]} -gt 0 ]; then
  MESSAGE="SESSION EXIT WARNINGS:"
  for w in "${WARNINGS[@]}"; do
    MESSAGE="$MESSAGE
  - $w"
  done
  python3 -c 'import json, sys; print(json.dumps({"systemMessage": sys.argv[1]}))' "$MESSAGE"
fi

exit 0
