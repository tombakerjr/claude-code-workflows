#!/bin/bash
#
# Stop Check Hook - Runs when Claude session ends
# Warns about uncommitted changes, open PRs, and other issues.
#
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
cd "$PROJECT_DIR"

WARNINGS=""

# Check uncommitted changes
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  WARNINGS="$WARNINGS\n  - Uncommitted changes exist"
fi

# Check for open PR on current branch
PR_STATE=$(gh pr view --json state -q '.state' 2>/dev/null || echo "NONE")
if [ "$PR_STATE" = "OPEN" ]; then
  PR_NUM=$(gh pr view --json number -q '.number' 2>/dev/null)
  WARNINGS="$WARNINGS\n  - PR #$PR_NUM is still OPEN - complete merge workflow?"
fi

# Check if on main branch with changes
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    WARNINGS="$WARNINGS\n  - ON MAIN BRANCH with uncommitted changes - create feature branch!"
  fi
fi

# Output warnings if any
if [ -n "$WARNINGS" ]; then
  echo -e "SESSION EXIT WARNINGS:$WARNINGS" >&2
fi

exit 0
