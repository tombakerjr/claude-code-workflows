#!/bin/bash
cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Use agent-team-development for plan execution (falls back to subagent-driven-development if agent teams not enabled). Never commit to main. For new features: dev-workflow:brainstorming. For bugs: dev-workflow:systematic-debugging."
  }
}
EOF
