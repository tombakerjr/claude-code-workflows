#!/usr/bin/env python3
"""
Git Guard Hook - PreToolUse hook for Bash commands
Blocks dangerous git operations and warns on PR merges.

This hook scans bash commands and:
1. BLOCKS direct pushes to main/master branches
2. BLOCKS commits when on main/master branch
3. WARNS when using raw `gh pr merge` (recommends /pr-merge command)

Usage: Configure in hooks/hooks.json
"""
import json
import sys
import re
import subprocess


def parse_git_c_path(command):
    """Extract the -C <path> argument from a git command, if present."""
    # Handle both quoted and unquoted paths: git -C "path with spaces" or git -C path
    match = re.search(r'git\s+-C\s+(?:"([^"]+)"|(\S+))', command)
    if match:
        return match.group(1) if match.group(1) else match.group(2)
    return None


def get_current_branch(cwd=None):
    """Get current git branch name, optionally for a specific directory."""
    try:
        cmd = ["git"]
        if cwd:
            cmd += ["-C", cwd]
        cmd += ["rev-parse", "--abbrev-ref", "HEAD"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


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

    # Block commits on main/master branch
    # Match git commit at the start of the command or after shell operators (&&, ;, |)
    # but NOT inside heredocs or string arguments (no re.MULTILINE — ^ only matches string start)
    if re.search(r'(?:^|&&|;|\|)\s*git\s+(-C\s+(?:"[^"]+"|(\S+))\s+)?commit', command):
        worktree_path = parse_git_c_path(command)
        branch = get_current_branch(cwd=worktree_path)
        if branch in ["main", "master"]:
            print("❌ BLOCKED: Cannot commit directly to main/master branch", file=sys.stderr)
            print("", file=sys.stderr)
            print("Create a feature branch first:", file=sys.stderr)
            print("  git checkout -b feature/your-feature-name", file=sys.stderr)
            print("", file=sys.stderr)
            print("Or use /feature-start if available", file=sys.stderr)
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
