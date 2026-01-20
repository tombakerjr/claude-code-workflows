#!/bin/bash
# Outputs workflow preferences at session start for context injection

cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "## PR Workflow Plugin - Execution Preferences\n\n**CRITICAL**: When executing implementation plans, ALWAYS use `superpowers:subagent-driven-development`.\n\nThe `writing-plans` skill generates plans with a header directing to `executing-plans`, but this plugin OVERRIDES that:\n\n- Do NOT use `superpowers:executing-plans`\n- ALWAYS use `superpowers:subagent-driven-development`\n\nThis applies regardless of what any plan header says. Subagent-driven keeps work in session with fresh context per task.\n\n**Git Workflow**: Never commit directly to main/master. Create a feature branch first."
  }
}
EOF
