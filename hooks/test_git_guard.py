#!/usr/bin/env python3
"""Unit tests for git-guard hook helpers.

Run with: python3 -m unittest hooks/test_git_guard.py

Tests use stdlib only (no pytest required) so they can run anywhere
Python 3 is available.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch


_HERE = os.path.dirname(os.path.abspath(__file__))
_GIT_GUARD_PATH = os.path.join(_HERE, "git-guard.py")
_spec = importlib.util.spec_from_file_location("git_guard", _GIT_GUARD_PATH)
git_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(git_guard)


class MergeWarningKeyTests(unittest.TestCase):
    """Covers the PR-number / repo-slug extraction. The key shape is
    `merge:<owner/repo>/<pr_num>`, and the same (session, key) tuple
    must collapse to one warning."""

    def _key(self, command):
        # Stub get_repo_slug so tests don't depend on a real gh/git env
        with patch.object(git_guard, "get_repo_slug", return_value="owner/repo"):
            return git_guard.merge_warning_key(command)

    def test_pr_number_immediately_after_merge(self):
        self.assertEqual(self._key("gh pr merge 123"), "merge:owner/repo/123")

    def test_pr_number_after_flag(self):
        self.assertEqual(self._key("gh pr merge --squash 123"), "merge:owner/repo/123")

    def test_pr_number_after_repo_flag(self):
        self.assertEqual(
            self._key("gh pr merge --repo other/repo 99"),
            "merge:other/repo/99",
        )

    def test_pr_number_with_repo_equals_form(self):
        self.assertEqual(
            self._key("gh pr merge --repo=other/repo 42"),
            "merge:other/repo/42",
        )

    def test_pr_number_before_flags(self):
        self.assertEqual(
            self._key("gh pr merge 7 --squash --delete-branch"),
            "merge:owner/repo/7",
        )

    def test_no_pr_number_uses_current(self):
        self.assertEqual(
            self._key("gh pr merge --squash --auto"),
            "merge:owner/repo/current",
        )

    def test_no_pr_number_with_repo_uses_current(self):
        self.assertEqual(
            self._key("gh pr merge --repo other/repo --squash"),
            "merge:other/repo/current",
        )

    def test_distinct_prs_in_same_repo_produce_distinct_keys(self):
        a = self._key("gh pr merge --squash 11")
        b = self._key("gh pr merge --squash 22")
        self.assertNotEqual(a, b)

    def test_compound_command_with_preceding_git_merge_ignores_unrelated_int(self):
        # Regression: a `merge` token from `git merge` upstream of `gh pr merge`
        # must not be picked up as the PR number. Only the gh→pr→merge sequence
        # opens the arg-parsing window.
        self.assertEqual(
            self._key("git merge 123 && gh pr merge"),
            "merge:owner/repo/current",
        )

    def test_compound_command_with_following_pr_number(self):
        self.assertEqual(
            self._key("git merge 123 && gh pr merge 456"),
            "merge:owner/repo/456",
        )

    def test_unrelated_command_with_merge_token_returns_current(self):
        # If `gh pr merge` is not in the command at all, we should not
        # synthesize a PR number from some other `merge` usage.
        self.assertEqual(
            self._key("git merge feature/foo"),
            "merge:owner/repo/current",
        )


class ResolveCommitDirTests(unittest.TestCase):
    """Covers per-invocation directory resolution for the main-branch commit
    block. The resolution must be scoped to the specific `git commit` that
    matched: its own `-C` wins, then the last `cd` BEFORE it, never an
    unrelated `-C`/`cd` elsewhere in a compound command."""

    def _resolve(self, command):
        m = git_guard.COMMIT_RE.search(command)
        self.assertIsNotNone(m, f"COMMIT_RE did not match: {command}")
        return git_guard.resolve_commit_dir(command, m)

    def test_plain_commit_uses_hook_cwd(self):
        self.assertIsNone(self._resolve("git commit -m x"))

    def test_dash_c_on_the_commit_invocation(self):
        self.assertEqual(self._resolve("git -C /wt commit -m x"), "/wt")

    def test_dash_c_quoted_path_with_spaces(self):
        self.assertEqual(
            self._resolve('git -C "/my worktree" commit -m x'), "/my worktree"
        )

    def test_unrelated_earlier_dash_c_is_ignored(self):
        # Regression (false-allow): `git -C /other-repo status && git commit`
        # must NOT resolve the commit's branch from /other-repo — the commit
        # itself runs in the hook's cwd.
        self.assertIsNone(
            self._resolve("git -C /other-repo status && git commit -m x")
        )

    def test_leading_cd_before_commit(self):
        self.assertEqual(
            self._resolve("cd /wt && git commit -m x"), "/wt"
        )

    def test_cd_then_semicolon(self):
        self.assertEqual(
            self._resolve("cd /wt; git commit -m x"), "/wt"
        )

    def test_cd_quoted_path_with_spaces(self):
        self.assertEqual(
            self._resolve('cd "/my worktree" && git commit -m x'), "/my worktree"
        )

    def test_last_cd_before_commit_wins(self):
        self.assertEqual(
            self._resolve("cd /a && cd /b && git commit -m x"), "/b"
        )

    def test_cd_after_commit_is_ignored(self):
        # Regression (false-allow): `git commit && cd /wt && ls` — the cd runs
        # after the commit and must not influence the branch check.
        self.assertIsNone(self._resolve("git commit -m x && cd /wt && ls"))

    def test_dash_c_on_commit_beats_earlier_cd(self):
        self.assertEqual(
            self._resolve("cd /a && git -C /b commit -m x"), "/b"
        )

    def test_earlier_dash_c_does_not_shadow_cd_resolution(self):
        # Regression (false-block): `git -C . status && cd /wt && git commit`
        # must resolve /wt (the cd), not `.` from the unrelated status call.
        self.assertEqual(
            self._resolve("git -C . status && cd /wt && git commit -m x"), "/wt"
        )

    def test_bare_trailing_cd_is_not_a_directory_change(self):
        # `cd /wt` with nothing chained after it doesn't change the directory
        # for a later command in this string (there is none).
        self.assertIsNone(self._resolve("git commit -m x; cd /wt"))

    def test_cd_inside_double_quoted_string_is_ignored(self):
        # Regression (false-allow): a cd-shaped substring inside a quoted
        # argument never changes the shell's directory — the commit really
        # runs in the hook's cwd and must be checked there.
        self.assertIsNone(
            self._resolve('echo "note && cd /tmp && more" && git commit -m x')
        )

    def test_cd_inside_single_quoted_string_is_ignored(self):
        self.assertIsNone(
            self._resolve("echo 'a && cd /tmp && b' && git commit -m x")
        )

    def test_real_cd_with_quoted_string_earlier_still_resolves(self):
        # Quote-awareness must not disable legitimate cds elsewhere in the
        # same command.
        self.assertEqual(
            self._resolve('echo "cd /decoy &&" && cd /wt && git commit -m x'),
            "/wt",
        )


class ResolveWorktreePathTests(unittest.TestCase):
    """Covers resolving a relative path against CLAUDE_PROJECT_DIR, with
    graceful fallback when it isn't set."""

    def test_none_passthrough(self):
        self.assertIsNone(git_guard.resolve_worktree_path(None))

    def test_absolute_path_passthrough(self):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/somewhere/else"}):
            self.assertEqual(
                git_guard.resolve_worktree_path("/abs/worktree"), "/abs/worktree"
            )

    def test_relative_path_resolved_against_project_dir(self):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/proj"}):
            self.assertEqual(
                git_guard.resolve_worktree_path(".worktrees/feature-x"),
                os.path.join("/proj", ".worktrees/feature-x"),
            )

    def test_relative_path_without_project_dir_passthrough(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                git_guard.resolve_worktree_path(".worktrees/feature-x"),
                ".worktrees/feature-x",
            )


class GitGuardHookIntegrationTests(unittest.TestCase):
    """End-to-end: invokes git-guard.py exactly as Claude Code would (JSON
    on stdin, exit code + stderr as the verdict), against real temporary git
    repos. Regression coverage for the worktree false-block (`cd <worktree>
    && git commit` used to be checked against the hook's own cwd) and for
    the unscoped `-C`/`cd` hijack cases."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="git-guard-test-")
        self._run_git(["init", "-q"])
        self._run_git(["checkout", "-q", "-b", "main"])
        self._run_git(["config", "user.email", "test@example.com"])
        self._run_git(["config", "user.name", "Test"])
        self._run_git(["commit", "-q", "--allow-empty", "-m", "init"])

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _run_git(self, args, cwd=None):
        subprocess.run(
            ["git", "-C", cwd or self.repo] + args, check=True, capture_output=True
        )

    def _invoke_hook(self, command, cwd=None, env=None):
        payload = json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "session_id": "test-session",
            }
        )
        # Control CLAUDE_PROJECT_DIR explicitly: strip any inherited value so
        # resolution behavior is deterministic, then apply the test's env.
        run_env = dict(os.environ)
        run_env.pop("CLAUDE_PROJECT_DIR", None)
        if env:
            run_env.update(env)
        return subprocess.run(
            [sys.executable, _GIT_GUARD_PATH],
            input=payload,
            capture_output=True,
            text=True,
            cwd=cwd or self.repo,
            env=run_env,
            timeout=10,
        )

    def _add_worktree(self, name, branch=None):
        worktree = os.path.join(self.repo, ".worktrees", name)
        args = ["worktree", "add", "-q", worktree]
        if branch:
            args += ["-b", branch]
        else:
            args += ["main"]
        self._run_git(args)
        return worktree

    def test_push_to_main_is_blocked(self):
        result = self._invoke_hook("git push origin main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_push_to_feature_branch_is_allowed(self):
        result = self._invoke_hook("git push origin feature/whatever")
        self.assertEqual(result.returncode, 0)

    def test_commit_on_main_is_blocked(self):
        result = self._invoke_hook('git commit -m "test"')
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_commit_on_feature_branch_is_allowed(self):
        self._run_git(["checkout", "-q", "-b", "feature/on-main-repo"])
        result = self._invoke_hook('git commit -m "test"')
        self.assertEqual(result.returncode, 0)

    def test_explicit_dash_c_worktree_on_feature_branch_is_allowed(self):
        worktree = self._add_worktree("feature-x", branch="feature/test-branch")
        result = self._invoke_hook(f'git -C {worktree} commit -m "test"')
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_cd_into_worktree_on_feature_branch_is_allowed(self):
        # Regression: `cd <worktree> && git commit` on a legitimate feature
        # branch used to be blocked because the branch check fell back to
        # the hook's own cwd (the outer repo, on `main`).
        worktree = self._add_worktree("feature-x", branch="feature/test-branch")
        result = self._invoke_hook(f'cd {worktree} && git commit -m "test"')
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_cd_into_worktree_that_is_on_main_is_still_blocked(self):
        # Confirms the fix resolves the *worktree's* branch correctly rather
        # than simply never blocking cd-prefixed commands. Move the outer
        # repo off `main` first (git disallows the same branch checked out
        # in two worktrees at once) — if resolution fell back to the hook's
        # own cwd it would read `feature/outer` and wrongly allow this.
        self._run_git(["checkout", "-q", "-b", "feature/outer"])
        worktree = self._add_worktree("on-main")
        result = self._invoke_hook(f'cd {worktree} && git commit -m "test"')
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_unrelated_dash_c_does_not_bypass_main_block(self):
        # Regression (false-allow): an earlier `git -C <feature-worktree>`
        # on a *different* invocation must not launder a bare `git commit`
        # that actually runs in the hook's cwd on main.
        worktree = self._add_worktree("feature-x", branch="feature/test-branch")
        result = self._invoke_hook(
            f'git -C {worktree} status && git commit -m "test"'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_cd_after_commit_does_not_bypass_main_block(self):
        # Regression (false-allow): a cd that runs after the commit must not
        # influence the branch check for that commit.
        worktree = self._add_worktree("feature-x", branch="feature/test-branch")
        result = self._invoke_hook(f'git commit -m "test" && cd {worktree} && ls')
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_earlier_dash_c_does_not_false_block_cd_worktree_commit(self):
        # Regression (false-block): `git -C . status && cd <worktree> && git
        # commit` must resolve the worktree's branch, not `.` from the
        # unrelated status call.
        worktree = self._add_worktree("feature-x", branch="feature/test-branch")
        result = self._invoke_hook(
            f'git -C . status && cd {worktree} && git commit -m "test"'
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_cd_inside_quoted_string_does_not_launder_main_commit(self):
        # Regression for the review CRITICAL: the embedded `cd /tmp` never
        # executes (it's inside the echo string), so the commit genuinely
        # runs on main and must be blocked — previously the false cd match
        # resolved to a non-repo dir, the branch lookup returned None, and
        # the guard failed open.
        result = self._invoke_hook(
            'echo "note && cd /tmp && more" && git commit -m "x"'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_nonexistent_worktree_path_fails_closed(self):
        # A real cd to a path that isn't a usable git repo must fall back
        # to checking the hook's own cwd (main here), not silently allow.
        result = self._invoke_hook(
            'cd .worktrees/does-not-exist && git commit -m "x"'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_quoted_git_commit_text_is_not_a_commit(self):
        # False-block guard: `git commit` appearing inside a string argument
        # (e.g. echoed advice) is not a real invocation and must be allowed
        # even on main.
        result = self._invoke_hook('echo "review, then && git commit -m done"')
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_cd_into_worktree_with_relative_path_resolves_via_project_dir(self):
        # The hook process's own cwd is deliberately NOT the repo here, so
        # this only passes if CLAUDE_PROJECT_DIR is actually being used to
        # resolve the relative `cd` target, not some cwd coincidence.
        self._add_worktree("feature-x", branch="feature/test-branch")
        unrelated_dir = tempfile.mkdtemp(prefix="git-guard-unrelated-")
        try:
            result = self._invoke_hook(
                'cd .worktrees/feature-x && git commit -m "test"',
                cwd=unrelated_dir,
                env={"CLAUDE_PROJECT_DIR": self.repo},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
        finally:
            shutil.rmtree(unrelated_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
