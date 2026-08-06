#!/usr/bin/env python3
"""Tests for the workflow-preferences.sh SessionStart hook's remote scoping.

Run with: python3 -m unittest hooks/test_workflow_preferences.py

The hook is a shell script, not a Python module, so these invoke it exactly
as Claude Code would (subprocess, cwd = the target repo) against real
temporary git repos with different `origin` remotes, rather than importing
it or re-implementing its matching logic as a separate "testable helper."
This is the pragmatic option the review called out: fewer moving parts to
keep in sync with the actual script.

Stdlib only — no pytest required.
"""
import json
import os
import subprocess
import tempfile
import shutil
import unittest


_HERE = os.path.dirname(os.path.abspath(__file__))
_HOOK_PATH = os.path.join(_HERE, "workflow-preferences.sh")


class WorkflowPreferencesRemoteScopingTests(unittest.TestCase):
    """The hook must only inject its additionalContext in Tom's own
    tombakerjr/* GitHub repos — everywhere else (Quantum work repos, forks,
    repos with no remote at all) it must stay silent so it doesn't compete
    with a user-scope CLAUDE.md that already sets these preferences."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="workflow-prefs-test-")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _set_origin(self, url):
        subprocess.run(
            ["git", "remote", "add", "origin", url], cwd=self.repo, check=True
        )

    def _invoke_hook(self):
        return subprocess.run(
            ["bash", _HOOK_PATH],
            cwd=self.repo,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_https_tombakerjr_remote_injects_context(self):
        self._set_origin("https://github.com/tombakerjr/claude-code-workflows.git")
        result = self._invoke_hook()
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "plan-execution",
            payload["hookSpecificOutput"]["additionalContext"],
        )

    def test_ssh_tombakerjr_remote_injects_context(self):
        self._set_origin("git@github.com:tombakerjr/some-personal-repo.git")
        result = self._invoke_hook()
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn(
            "plan-execution",
            payload["hookSpecificOutput"]["additionalContext"],
        )

    def test_never_commit_to_main_line_was_dropped(self):
        # git-guard.py already enforces this structurally; restating it in
        # the injected context was redundant even when in scope.
        self._set_origin("https://github.com/tombakerjr/claude-code-workflows.git")
        result = self._invoke_hook()
        payload = json.loads(result.stdout)
        self.assertNotIn(
            "Never commit to main",
            payload["hookSpecificOutput"]["additionalContext"],
        )

    def test_quantum_work_remote_is_silent(self):
        self._set_origin("https://github.com/camino-financial/quantum-hub.git")
        result = self._invoke_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_other_github_org_is_silent(self):
        self._set_origin("https://github.com/someone-else/their-repo.git")
        result = self._invoke_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_no_origin_remote_is_silent_and_does_not_error(self):
        # No `git remote add` at all — the hook must handle this gracefully.
        result = self._invoke_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
