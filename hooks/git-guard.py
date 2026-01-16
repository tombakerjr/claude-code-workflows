#!/usr/bin/env python3
"""
Git Guard Hook - PreToolUse hook for Bash commands
Blocks dangerous git operations and warns on PR merges.

This hook scans bash commands and:
1. BLOCKS direct pushes to main/master branches
2. WARNS when using raw `gh pr merge` (recommends /pr-merge command)

Usage: Configure in hooks/hooks.json
"""
import json
import sys
import re


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")

    # Patterns that should be blocked entirely
    blocked = [
        (r'git\s+push\s+.*\b(main|master)(\s|$)',
         "BLOCKED: Direct push to main/master. Use PR workflow."),
    ]

    for pattern, msg in blocked:
        if re.search(pattern, command, re.IGNORECASE):
            print(msg, file=sys.stderr)
            print(f"Command: {command}", file=sys.stderr)
            sys.exit(2)

    # Warn on gh pr merge without using /pr-merge command
    if re.search(r'gh\s+pr\s+merge', command):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    "WARNING: You are merging a PR. Did you complete the checklist?\n"
                    "1) Wait for CI to pass\n"
                    "2) Wait 10-12 seconds for delayed review comments\n"
                    "3) Fetch and review all comments\n"
                    "4) Address any blockers (CRITICAL, FIX, BLOCKER)\n"
                    "Consider using /pr-merge command instead for safe merging."
                )
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
