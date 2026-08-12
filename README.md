# Git Guardrails Plugin for Claude Code

Deterministic git guardrails for Claude Code. Two hooks, no prompt scaffolding:

- **Never commit or push to main/master** — blocked structurally, with worktree-aware
  branch resolution
- **Never merge a PR blind** — a one-time warning per PR reminds you to verify CI and
  the latest review before `gh pr merge` proceeds
- **Never walk away from uncommitted work** — a non-blocking warning when a session
  stops with a dirty tree or an open PR

## Philosophy

This plugin used to be much bigger: six workflow skills, seven reviewer/implementer
agents, model-routing tables, context-injection hooks. All of that was removed in v3.

The reasoning: prescriptive scaffolding written for older models actively degrades
output on current ones. Anthropic's [model prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
says instructions carried over from prompts tuned for earlier models should be
removed rather than rewritten, and Claude Code's creator [recommends](https://www.ycrootaccess.com/p/boris-cherny-building-claude-code)
periodically deleting your CLAUDE.md, skills, and hooks to see what the model does
without them — Anthropic itself deleted more than 80% of Claude Code's system prompt
for Opus 5 and measured an improvement.

What survives that test here is the part a model can't self-enforce: **hard,
deterministic checks with exit codes**. A hook that blocks a commit to main works
whether or not the model is having a good day. That's the bar for anything added to
this plugin — a reproducible failure, caught deterministically. Instructions asking
the model to behave don't qualify.

The pre-v3 machinery is preserved in git history (v2.x) if you need to resurrect
any of it.

## Installation

### Option 1: Direct from GitHub (Recommended)

```bash
/plugin marketplace add tombakerjr/claude-code-workflows
/plugin install dev-workflow@claude-code-workflows
```

Then restart Claude Code.

### Option 2: From Local Clone

```bash
git clone https://github.com/tombakerjr/claude-code-workflows.git
/plugin marketplace add /path/to/claude-code-workflows
/plugin install dev-workflow@tombakerjr-claude-tools
```

Then restart Claude Code.

## Hooks

| Hook | Event | Function |
|------|-------|----------|
| `git-guard.py` | PreToolUse:Bash | Blocks commits on main/master (worktree-aware: resolves the branch for each `git commit` via its own `-C <path>` or the last preceding `cd <path> &&`), blocks push to main/master, warns once per (session, PR) on `gh pr merge` |
| `stop-check.sh` | Stop | Emits a `systemMessage` warning for uncommitted changes, open PRs, or dirty main |

Both dispatch through `run-hook.cmd`, a batch/bash polyglot that works on
macOS, Linux, and Windows (Git Bash).

### PR merge verification

The merge warning points at the SHA-anchored review protocol: before merging,
CI must pass (`gh pr checks <pr> --watch`) and the latest `claude[bot]` sticky
review comment must be for the current head commit — parse
`**Reviewed commit:** <short-sha>` from the comment and compare to
`gh pr view <pr> --json headRefOid -q .headRefOid`. The
`claude-code-review.yml` workflow in this repo stamps that SHA into its
review comments.

## Testing

```bash
python3 -m unittest hooks.test_git_guard   # use `python` on Windows
bash -n hooks/stop-check.sh
```

Tests are stdlib-only (no pytest) and include end-to-end coverage that invokes
the hook exactly as Claude Code does, against real temporary git repos.

## License

MIT
