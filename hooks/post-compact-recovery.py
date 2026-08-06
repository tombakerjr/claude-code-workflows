#!/usr/bin/env python3
"""
Post-Compact Recovery Hook - PostCompact hook for automatic state re-assertion.

Compaction paraphrases whatever was in the conversation history, including
any additionalContext a PreCompact hook injected — this plugin's own
CLAUDE.md has a "Compaction Hints" section listing exactly this kind of
state (branch, uncommitted changes, open PR) as worth preserving, but had
no enforcement beyond hoping Claude re-derives it from the summary.

PostCompact runs AFTER compaction completes, and its additionalContext is
injected fresh for the next model request rather than being folded into
whatever just got summarized — a materially more reliable place to
re-assert this state than a PreCompact injection or CLAUDE.md prose. This
makes the git/PR portion of /context-recovery's Quick Recovery effectively
automatic after every compaction.

Every check here is best-effort: short timeouts and broad exception
handling throughout. This hook must never block, delay, or fail
compaction recovery — worst case on any error is simply no
additionalContext for this compaction.

Usage: Configure in hooks/hooks.json as a PostCompact hook.
"""
import json
import subprocess
import sys


def _run(cmd, timeout=3):
    """Run a command, returning stripped stdout on success or None on any
    failure (non-zero exit, timeout, missing binary, etc.)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def build_summary():
    """Collect a short list of state fragments. Never raises."""
    parts = []

    branch = _run(["git", "branch", "--show-current"])
    if branch:
        parts.append(f"branch: {branch}")

    status = _run(["git", "status", "--porcelain"])
    if status:
        count = len([line for line in status.splitlines() if line.strip()])
        if count:
            parts.append(f"{count} uncommitted change(s)")

    pr_json = _run(["gh", "pr", "view", "--json", "number,title,state"])
    if pr_json:
        try:
            pr = json.loads(pr_json)
            if pr.get("state") == "OPEN":
                parts.append(f"PR #{pr.get('number')} OPEN: {pr.get('title')}")
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return parts


def main():
    # Drain stdin so Claude Code's write doesn't race a closed pipe, matching
    # the pattern in the other hooks in this plugin.
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass

    try:
        parts = build_summary()
    except Exception:
        parts = []

    if not parts:
        sys.exit(0)

    context = "Post-compaction state recovery: " + "; ".join(parts)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostCompact",
            "additionalContext": context,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
