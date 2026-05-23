# CLAUDE.md

This file provides guidance to Claude Code when working with this plugin.

## Overview

This is a comprehensive Claude Code plugin that supports the full development workflow:
- **Planning**: Brainstorming, specification, and implementation planning
- **Implementation**: Test-driven development, systematic debugging, and subagent-driven execution
- **Review**: Comprehensive code reviews with multiple agent tiers
- **Merge**: Pre-commit verification + git guardrails. PR review verification (SHA-anchored protocol) lives in consuming projects' CLAUDE.md + memory, not in this plugin.

## Plugin Structure

```
claude-code-pr-workflow/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # For direct installation
├── agents/                  # Subagents
│   ├── code-verifier.md          # Pre-commit checks (typecheck + security scan)
│   ├── implementer.md            # Implementation agent for plan-execution
│   ├── pr-verifier.md            # Pre-merge CI/comment verification
│   ├── quality-reviewer.md       # Quick code-quality gate
│   ├── quick-reviewer.md         # Combined spec+quality review for simple tasks
│   ├── spec-reviewer.md          # Verify implementation matches spec
│   └── staff-code-reviewer.md    # Comprehensive staff/principal review
├── commands/               # Slash commands
│   └── context-recovery.md       # /context-recovery
├── skills/                 # Workflow skills
│   ├── agent-team-development/        # Parallel agent teams (preferred)
│   ├── subagent-driven-development/   # Sequential subagent execution (fallback)
│   ├── test-driven-development/       # TDD workflow
│   ├── systematic-debugging/          # Debug root cause analysis
│   ├── writing-plans/                 # Create implementation plans
│   ├── using-git-worktrees/           # Isolated git worktrees
│   └── brainstorming/                 # Design dialogue for features
├── hooks/                  # Event handlers
│   ├── hooks.json             # Hook configuration
│   ├── run-hook.cmd           # Cross-platform wrapper
│   ├── git-guard.py           # PreToolUse: block main push
│   ├── task-completed-gate.py # TaskCompleted: review gate for agent teams
│   └── stop-check.sh          # Stop: warn on uncommitted
├── CLAUDE.md
└── README.md
```

## Development

### Testing Changes

1. Make changes to plugin files
2. Run `claude plugin update`
3. Restart Claude Code for hooks to take effect

### Adding New Components

- **New command**: Create `commands/name.md` with frontmatter
- **New agent**: Create `agents/name.md` with frontmatter
- **New skill**: Create `skills/skill-name/` directory with `skill.md` and supporting files
- **New hook**: Add to `hooks/hooks.json`, create script in `hooks/`

### Cross-Platform Hooks

Use `run-hook.cmd` wrapper for all hook scripts:
```json
{
  "type": "command",
  "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" your-script.sh"
}
```

This ensures hooks work on Windows, macOS, and Linux.

### Version Bumps

When releasing:
1. Update `version` in `.claude-plugin/plugin.json`
2. Update `version` in `.claude-plugin/marketplace.json`
3. Commit and tag: `git tag v1.x.x`
4. Push: `git push && git push --tags`

## Key Workflows

### PR Review Verification (Why This Matters)

Before merging a PR, verify the latest review comment was generated for the **current head commit**. The plugin's `claude-code-review.yml` workflow template stamps the head SHA into the comment body (`**Reviewed commit:** <short-sha>`). Downstream verification should parse that and compare against `gh pr view --json headRefOid`. Never trust absence or staleness of the comment as approval — timestamp-only checks fail under CI re-runs without a fresh push.

The full SHA-anchored verification protocol belongs in each consuming project's CLAUDE.md and per-project memory file, since the bot author identifier and any project-specific quirks vary per repo.

### Agent Invocation

Agents are invoked automatically based on their descriptions or explicitly:
- "Run the code-verifier agent" - Pre-commit checks
- "Use staff-code-reviewer to review my changes" - Full code review
- "Check if this PR is safe to merge" - PR verification

### Skill Invocation

Skills provide structured workflows for common development tasks:
- "Use dev-workflow:brainstorming" - Start design dialogue for new features
- "Use dev-workflow:systematic-debugging" - Debug with root cause analysis
- "Use dev-workflow:writing-plans" - Create implementation plan with tasks
- "Use dev-workflow:agent-team-development" - Execute plans with parallel agent teams (preferred, falls back to subagent-driven-development)
- "Use dev-workflow:subagent-driven-development" - Execute implementation plans with sequential subagents (fallback)
- "Use dev-workflow:test-driven-development" - TDD workflow with test-first approach
- "Use dev-workflow:using-git-worktrees" - Isolated git worktrees for complex features

## Customization

Users should customize:
1. Review criteria in `staff-code-reviewer.md`
2. Blocked patterns in `git-guard.py`

## Compaction Hints

When compacting conversation history, preserve:
- Current task and phase number
- Git branch and last commit SHA
- Any blockers or review feedback not yet addressed
- PR number if one exists
- Active teammate names and worktree paths (if using agent teams)

Discard:
- Full file contents (can re-read)
- Verbose build/test output
- Completed task details (just "Task N: complete")

## Token Efficiency

- Clear between unrelated tasks with /clear
- Compact at 50-80% capacity, don't wait for auto-compact at 95%
- Have subagents read files themselves rather than passing content inline
