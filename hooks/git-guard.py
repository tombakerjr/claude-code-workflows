#!/usr/bin/env python3
"""
Git Guard Hook - PreToolUse hook for Bash commands
Blocks dangerous git operations and warns on PR merges.

This hook scans bash commands and:
1. BLOCKS direct pushes to main/master branches
2. BLOCKS commits when on main/master branch
3. WARNS on first PR-merge attempt per session+PR (BLOCK-then-allow-on-retry).
   After the warning fires once for a given (session, PR), subsequent attempts
   in the same session proceed silently. Pattern mirrors anthropics/claude-code's
   security-guidance plugin: warn without permanently preventing — confirm and
   try again.

Usage: Configure in hooks/hooks.json
"""
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime


WARNING_STATE_DIR = os.path.expanduser("~/.claude")


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


def get_repo_slug(cwd=None):
    """Get current repo's owner/name slug from gh CLI, or None on failure."""
    try:
        cmd = ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5, cwd=cwd
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def warning_state_file(session_id):
    """Per-session warning-state file path."""
    return os.path.join(WARNING_STATE_DIR, f"git_guard_warnings_{session_id}.json")


def load_shown_warnings(session_id):
    """Load the set of warning keys already shown in this session."""
    path = warning_state_file(session_id)
    if not os.path.exists(path):
        return set()
    try:
        with open(path) as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()


def save_shown_warnings(session_id, shown):
    """Persist the set of warning keys shown in this session."""
    path = warning_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(list(shown), f)
    except IOError:
        pass  # fail silently — state is best-effort


def cleanup_old_state_files():
    """Remove warning-state files older than 30 days. Called probabilistically."""
    try:
        if not os.path.exists(WARNING_STATE_DIR):
            return
        cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        for filename in os.listdir(WARNING_STATE_DIR):
            if filename.startswith("git_guard_warnings_") and filename.endswith(".json"):
                file_path = os.path.join(WARNING_STATE_DIR, filename)
                try:
                    if os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                except (OSError, IOError):
                    pass
    except Exception:
        pass


def merge_warning_key(command):
    """Build the dedup key for a PR-merge warning, based on repo+PR if available."""
    # Extract PR number from the command if present (gh pr merge <num> ...)
    pr_match = re.search(r'gh\s+pr\s+merge\s+(\d+)', command)
    pr_part = pr_match.group(1) if pr_match else "current"
    # Extract repo slug — prefer --repo flag, fall back to current repo, then unknown
    repo_match = re.search(r'--repo\s+(\S+)', command)
    if repo_match:
        repo_part = repo_match.group(1)
    else:
        repo_part = get_repo_slug() or "unknown-repo"
    return f"merge:{repo_part}/{pr_part}"


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    session_id = input_data.get("session_id", "default")

    # Periodically clean up old state files (10% chance per invocation)
    if random.random() < 0.1:
        cleanup_old_state_files()

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

    # Warn on PR-merge — remind about CI + review-comment SHA verification.
    # Anchor to start-of-command or shell-operator boundary to avoid false positives
    # on commit messages or other strings that mention the command verbatim.
    # First fire per (session, repo, PR): WARN + BLOCK. Retry: silent allow.
    if re.search(r'(?:^|&&|;|\|)\s*gh\s+pr\s+merge', command):
        key = merge_warning_key(command)
        shown = load_shown_warnings(session_id)
        if key not in shown:
            shown.add(key)
            save_shown_warnings(session_id, shown)
            print(
                "WARNING: You are merging a PR. Did you verify it's ready?\n"
                "1) CI passed: `gh pr checks <pr> --watch`\n"
                "2) Latest sticky review comment SHA matches PR head:\n"
                "   parse `**Reviewed commit:** <short-sha>` from the latest\n"
                "   claude[bot] comment; compare to `gh pr view <pr> --json headRefOid`\n"
                "3) Review has no CRITICAL / FIX / BLOCKER items\n"
                "See the project's CLAUDE.md / per-project memory for the full\n"
                "SHA-anchored verification protocol.\n"
                "\n"
                "If verified, re-issue the command to proceed.",
                file=sys.stderr,
            )
            sys.exit(2)
        # Already warned for this (session, repo, PR) — allow silently.

    sys.exit(0)


if __name__ == "__main__":
    main()
