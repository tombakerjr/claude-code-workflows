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


class ParseCdPathTests(unittest.TestCase):
    """Covers the `cd <path> &&`/`cd <path>;` extraction used to resolve
    which worktree a command is operating in (issue #7's residual gap:
    only `-C <path>` was parsed, not a leading `cd`)."""

    def test_cd_then_double_ampersand(self):
        self.assertEqual(
            git_guard.parse_cd_path("cd .worktrees/feature-x && git commit -m x"),
            ".worktrees/feature-x",
        )

    def test_cd_then_semicolon(self):
        self.assertEqual(
            git_guard.parse_cd_path("cd .worktrees/feature-x; git commit -m x"),
            ".worktrees/feature-x",
        )

    def test_quoted_path_with_spaces(self):
        self.assertEqual(
            git_guard.parse_cd_path('cd "my worktree" && git commit -m x'),
            "my worktree",
        )

    def test_cd_after_shell_operator(self):
        self.assertEqual(
            git_guard.parse_cd_path(
                "git status && cd .worktrees/feature-x && git commit -m x"
            ),
            ".worktrees/feature-x",
        )

    def test_no_leading_cd_returns_none(self):
        self.assertIsNone(git_guard.parse_cd_path("git commit -m x"))

    def test_cd_without_following_operator_returns_none(self):
        # A bare `cd path` with nothing chained after it isn't a compound
        # command changing directory for a subsequent git call.
        self.assertIsNone(git_guard.parse_cd_path("cd .worktrees/feature-x"))

    def test_cd_mentioned_later_is_not_the_leading_cd(self):
        # `cd` appearing only inside a later clause (not itself preceded by
        # a boundary matching this command's structure) should not match as
        # if it were the leading directory change of the whole command.
        # Here it *is* preceded by `&&`, so this documents current (correct)
        # behavior: any cd-then-operator segment counts, not just position 0.
        self.assertEqual(
            git_guard.parse_cd_path("true && cd worktree && git commit -m x"),
            "worktree",
        )


class ResolveWorktreePathTests(unittest.TestCase):
    """Covers resolving a `cd`-derived relative path against
    CLAUDE_PROJECT_DIR, with graceful fallback when it isn't set."""

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
    repos. This is the regression coverage for the worktree false-block:
    `cd .worktrees/x && git commit` used to check this hook process's own
    cwd instead of the worktree's actual branch."""

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
        run_env = dict(os.environ)
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
        # Sanity check: the pre-existing `-C <path>` resolution still works.
        worktree = os.path.join(self.repo, ".worktrees", "feature-x")
        self._run_git(["worktree", "add", "-q", worktree, "-b", "feature/test-branch"])
        result = self._invoke_hook(f'git -C {worktree} commit -m "test"')
        self.assertEqual(result.returncode, 0)

    def test_cd_into_worktree_on_feature_branch_is_allowed(self):
        # Regression test for the false-block found during review: a
        # `cd <worktree> && git commit` on a legitimate feature branch used
        # to be blocked because only `-C <path>` was resolved, so the
        # branch check fell back to this hook's own cwd (the outer repo,
        # on `main`) instead of the worktree's actual branch.
        worktree = os.path.join(self.repo, ".worktrees", "feature-x")
        self._run_git(["worktree", "add", "-q", worktree, "-b", "feature/test-branch"])
        result = self._invoke_hook(f'cd {worktree} && git commit -m "test"')
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_cd_into_worktree_that_is_on_main_is_still_blocked(self):
        # Confirms the fix resolves the *worktree's* branch correctly rather
        # than simply never blocking cd-prefixed commands. Move the outer
        # repo off `main` first (git disallows the same branch checked out
        # in two worktrees at once) — if the resolution were still buggy and
        # fell back to the hook's own cwd, it would read `feature/outer` and
        # wrongly allow this, so this also proves it isn't a coincidence.
        self._run_git(["checkout", "-q", "-b", "feature/outer"])
        worktree = os.path.join(self.repo, ".worktrees", "on-main")
        self._run_git(["worktree", "add", "-q", worktree, "main"])
        result = self._invoke_hook(f'cd {worktree} && git commit -m "test"')
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)

    def test_cd_into_worktree_with_relative_path_resolves_via_project_dir(self):
        # The hook process's own cwd is deliberately NOT the repo here, so
        # this only passes if CLAUDE_PROJECT_DIR is actually being used to
        # resolve the relative `cd` target, not some cwd coincidence.
        self._run_git(
            ["worktree", "add", "-q", ".worktrees/feature-x", "-b", "feature/test-branch"]
        )
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
