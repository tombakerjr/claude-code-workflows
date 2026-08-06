#!/bin/bash
#
# SessionStart hook - injects dev-workflow execution preferences, but ONLY
# in Tom's own personal repos (matched by the `origin` remote). This plugin
# is also installed in Quantum work repos, where a user-scope CLAUDE.md
# already sets execution preferences of its own — injecting unconditionally
# here silently competed with that file. "Never commit to main" is
# deliberately omitted from the injected text: git-guard.py already enforces
# that structurally, so restating it here was redundant even in scope.
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"

if ! echo "$REMOTE_URL" | grep -qE 'github\.com[:/]tombakerjr/'; then
  exit 0
fi

cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Use plan-execution for executing implementation plans (selects agent teams or subagents automatically). For new features: dev-workflow:brainstorming. For bugs: dev-workflow:systematic-debugging."
  }
}
EOF
