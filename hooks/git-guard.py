#!/usr/bin/env python3
"""
Git Guard Hook - PreToolUse hook for Bash commands
Blocks dangerous git operations and warns on PR merges.

This hook scans bash commands and:
1. BLOCKS direct pushes to main/master branches
2. BLOCKS commits when on main/master branch. The branch is resolved per
   commit invocation: an explicit `git -C <path>` on that invocation wins,
   otherwise the last `cd <path> &&` preceding it, otherwise the hook's own
   cwd. This keeps a commit inside a worktree checked against the worktree's
   branch, and keeps an unrelated `-C`/`cd` elsewhere in a compound command
   from hijacking the check.
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
import shlex
import subprocess
import sys
from datetime import datetime


WARNING_STATE_DIR = os.path.expanduser("~/.claude")

# A `git commit` at the start of the command or after a shell operator
# (&&, ;, |) — not inside heredocs (no re.MULTILINE, so ^ only matches
# string start). Captures that invocation's own `-C <path>` if present
# (quoted or unquoted). Matches whose `git` keyword sits inside a quoted
# string (see quoted_mask) are skipped by the caller.
COMMIT_RE = re.compile(
    r'(?:^|&&|;|\|)\s*(?P<kw>git)\s+(?:-C\s+(?:"(?P<cq>[^"]+)"|(?P<cu>\S+))\s+)?commit\b'
)

# A directory change that affects subsequent commands: `cd <path>` at the
# start of the command or after a shell operator, followed by another
# operator. A trailing bare `cd` with nothing chained after it doesn't
# change the directory for a later git call and is ignored. The trailing
# operator is a lookahead (not consumed) so chained cds — `cd a && cd b &&`
# — don't swallow the boundary the next match needs. Matches whose `cd`
# keyword sits inside a quoted string (see quoted_mask) are skipped.
CD_RE = re.compile(
    r'(?:^|&&|;|\|)\s*(?P<kw>cd)\s+(?:"(?P<q>[^"]+)"|(?P<u>\S+))(?=\s*(?:&&|;))'
)


def quoted_mask(command):
    """Per-character flags: True where the character sits inside a single-
    or double-quoted region of the command.

    Approximate shell semantics — backslash escapes the next character
    outside single quotes and inside double quotes; single-quoted text is
    literal until the closing quote. Used to keep `cd`/`git commit`-shaped
    substrings inside string arguments (commit messages, echo text) from
    being mistaken for real invocations.
    """
    mask = [False] * len(command)
    quote = None
    i = 0
    while i < len(command):
        ch = command[i]
        if quote is None:
            if ch == "\\":
                i += 2
                continue
            if ch in ("'", '"'):
                quote = ch
                mask[i] = True
        else:
            mask[i] = True
            if ch == "\\" and quote == '"':
                if i + 1 < len(command):
                    mask[i + 1] = True
                i += 2
                continue
            if ch == quote:
                quote = None
        i += 1
    return mask


def resolve_worktree_path(path):
    """Resolve a possibly-relative path against CLAUDE_PROJECT_DIR.

    Absolute paths pass through unchanged. Relative paths resolve against
    CLAUDE_PROJECT_DIR when set; otherwise they're returned as-is and the
    subsequent `git -C <path>` call resolves them against this hook
    process's own cwd (the same fallback stop-check.sh uses).
    """
    if not path or os.path.isabs(path):
        return path
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        return path
    return os.path.join(project_dir, path)


def resolve_commit_dir(command, commit_match, mask=None):
    """Directory a matched `git commit` invocation will run in.

    Precedence: the invocation's own `-C <path>` (captured by COMMIT_RE),
    then the last `cd <path> &&` that appears BEFORE the invocation, then
    None (the hook's own cwd). A `cd` positioned after the commit — e.g.
    `git commit -m x && cd elsewhere` — runs after the commit and must not
    influence the check, and neither must a `cd`-shaped substring inside a
    quoted argument.
    """
    if mask is None:
        mask = quoted_mask(command)

    c_path = commit_match.group("cq") or commit_match.group("cu")
    if c_path:
        return resolve_worktree_path(c_path)

    last_cd = None
    for cd in CD_RE.finditer(command):
        if cd.start() >= commit_match.start():
            break
        if mask[cd.start("kw")]:
            continue
        last_cd = cd.group("q") or cd.group("u")
    if last_cd:
        return resolve_worktree_path(last_cd)
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
    """Build the dedup key for a PR-merge warning, based on repo+PR if available.

    The PR number can appear anywhere after the `merge` subcommand — before
    or after flags like `--squash` or `--repo owner/repo` — so we tokenize
    rather than rely on positional regex. The first bare-integer token after
    `merge` is the PR number; if none is present, `gh pr merge` operates on
    the current branch's PR and we use "current" as the key part.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    pr_part = "current"
    repo_part = None

    # Only enter arg-parsing after seeing the full `gh pr merge` subcommand
    # sequence. Without this, compound commands like `git merge 123 && gh pr
    # merge` would pick up `123` from the `git merge` operand.
    merge_idx = -1
    for j in range(len(tokens) - 2):
        if tokens[j] == "gh" and tokens[j + 1] == "pr" and tokens[j + 2] == "merge":
            merge_idx = j + 2
            break
    if merge_idx == -1:
        return f"merge:{get_repo_slug() or 'unknown-repo'}/current"

    i = merge_idx + 1
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--repo" and i + 1 < len(tokens):
            repo_part = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--repo="):
            repo_part = tok.split("=", 1)[1]
            i += 1
            continue
        if pr_part == "current" and tok.isdigit():
            pr_part = tok
        i += 1

    if not repo_part:
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

    # Block commits on main/master. Every commit invocation in a compound
    # command is checked against the directory it will actually run in.
    mask = quoted_mask(command)
    for commit_match in COMMIT_RE.finditer(command):
        if mask[commit_match.start("kw")]:
            # `git commit`-shaped text inside a quoted argument, not a
            # real invocation.
            continue
        commit_dir = resolve_commit_dir(command, commit_match, mask)
        branch = get_current_branch(cwd=commit_dir)
        if branch is None and commit_dir is not None:
            # Fail closed: a resolved directory that isn't a usable git
            # repo (typo'd worktree path, residual false match) must not
            # skip the check. Fall back to the hook's own cwd — the
            # pre-resolution behavior — rather than silently allowing.
            branch = get_current_branch()
        if branch in ["main", "master"]:
            print("❌ BLOCKED: Cannot commit directly to main/master branch", file=sys.stderr)
            print("", file=sys.stderr)
            print("Create a feature branch first:", file=sys.stderr)
            print("  git checkout -b feature/your-feature-name", file=sys.stderr)
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
