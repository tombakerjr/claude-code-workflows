#!/bin/bash
cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Use subagent-driven-development for plan execution. Never commit to main. For new features: dev-workflow:brainstorming. For bugs: dev-workflow:systematic-debugging."
  }
}
EOF
