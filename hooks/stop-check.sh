#!/bin/bash
#
# Stop Check Hook - Runs when Claude finishes a turn
# Warns about uncommitted changes, open PRs, and other issues.
#
# Warnings are surfaced via JSON {"systemMessage": "..."} on stdout (exit 0),
# which Claude Code shows to the user without blocking the stop. A prior
# version wrote these warnings to stderr on exit 0 — per the Stop hook
# contract, that goes only to the debug log, never the transcript, so none
# of those warnings ever actually reached anyone.
#
# The JSON is assembled with printf, no interpreter dependency: warning
# strings below must stay JSON-safe (no double quotes or backslashes).
# Line breaks are embedded as literal \n escape sequences.
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$PROJECT_DIR"

MSG=""

DIRTY="$(git status --porcelain 2>/dev/null || true)"
if [ -n "$DIRTY" ]; then
  MSG="$MSG\\n  - Uncommitted changes exist"
fi

# Check for open PR on current branch
PR_STATE="$(gh pr view --json state -q '.state' 2>/dev/null || echo NONE)"
if [ "$PR_STATE" = "OPEN" ]; then
  PR_NUM="$(gh pr view --json number -q '.number' 2>/dev/null || echo '?')"
  MSG="$MSG\\n  - PR #$PR_NUM is still OPEN - complete merge workflow?"
fi

# Check if on main branch with changes
BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  if [ -n "$DIRTY" ]; then
    MSG="$MSG\\n  - ON MAIN BRANCH with uncommitted changes - create feature branch!"
  fi
fi

if [ -n "$MSG" ]; then
  printf '{"systemMessage": "SESSION EXIT WARNINGS:%s"}\n' "$MSG"
fi

exit 0
