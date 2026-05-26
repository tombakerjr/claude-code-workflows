#!/usr/bin/env python3
"""Unit tests for git-guard hook helpers.

Run with: python3 -m unittest hooks/test_git_guard.py

Tests use stdlib only (no pytest required) so they can run anywhere
Python 3 is available.
"""
import importlib.util
import os
import unittest
from unittest.mock import patch


_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "git_guard", os.path.join(_HERE, "git-guard.py")
)
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


if __name__ == "__main__":
    unittest.main()
