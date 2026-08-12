# CLAUDE.md

This file provides guidance to Claude Code when working with this plugin.

## Overview

This plugin provides **deterministic git guardrails** and nothing else:

- `git-guard.py` (PreToolUse:Bash) — blocks commits/pushes to main/master,
  warns once per PR merge
- `stop-check.sh` (Stop) — surfaces uncommitted-work warnings when a
  session stops

## Design principle: enforcement, not coaching

Everything in this plugin must be a **hard, deterministic check** the model
cannot drift past. Behavioral coaching — skills that prescribe workflows,
reviewer-agent ladders, model-routing tables, context-injection hooks — was
deliberately removed in v3. Current Claude models do that work unprompted,
and Anthropic's guidance is that prescriptive scaffolding written for older
models degrades output quality on newer ones.

Before adding anything here, it must pass this bar:

1. It fires on a **reproducible failure** actually observed in practice
   (not a hypothetical), and
2. A hook can catch it **deterministically** (exit code, not prose asking
   the model to behave).

If a proposed addition is instructions rather than enforcement, it belongs
nowhere — not in this plugin, not in CLAUDE.md prose. Re-evaluate the
surviving hooks periodically too: run a week with the plugin uninstalled
(or `claude --safe-mode`) and keep only what was actually missed.

The pre-v3 machinery (6 skills, 7 agents, `/context-recovery`, SessionStart/
UserPromptSubmit/TaskCompleted hooks) lives in git history before the v3.0.0
release if something proves to be missed.

## Structure

```
claude-code-workflows/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata (version managed by release-please)
│   └── marketplace.json     # For direct installation
├── hooks/
│   ├── hooks.json           # Hook configuration
│   ├── run-hook.cmd         # Cross-platform dispatch wrapper (batch/bash polyglot)
│   ├── git-guard.py         # PreToolUse: block main commits/pushes, merge warning
│   ├── stop-check.sh        # Stop: warn on uncommitted work via systemMessage
│   └── test_git_guard.py    # Unit + integration tests (stdlib only)
├── CLAUDE.md
└── README.md
```

## Testing

```bash
python3 -m unittest hooks.test_git_guard
bash -n hooks/stop-check.sh
python3 -c "import json; json.load(open('hooks/hooks.json'))"
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
```

On Windows, run the unit tests with `python` (Git Bash's `python3` may be
the Microsoft Store stub). Shell hooks must stay free of `python3`/`jq`
dependencies — `run-hook.cmd` dispatches `.py` via `python` on Windows and
`.sh` via Git Bash, where only git, gh, and POSIX builtins are guaranteed.

## Releases

release-please manages versioning from Conventional Commit titles
(enforced on PRs by CI). It also bumps `.claude-plugin/plugin.json` —
never hand-edit the version. Keep `marketplace.json` descriptions in sync
with `plugin.json` when they change.
