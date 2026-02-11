# CLAUDE.md

This file provides guidance to Claude Code when working with this plugin.

## Overview

This is a comprehensive Claude Code plugin that supports the full development workflow:
- **Planning**: Brainstorming, specification, and implementation planning
- **Implementation**: Test-driven development, systematic debugging, and subagent-driven execution
- **Review**: Comprehensive code reviews with multiple agent tiers, CI watching, and review comment polling
- **Merge**: Git guardrails, readiness checks via `/pr-status`, and review-driven fix loops

## Plugin Structure

```
claude-code-pr-workflow/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # For direct installation
├── agents/                  # Subagents
│   ├── staff-code-reviewer.md  # Comprehensive review
│   ├── code-verifier.md        # Pre-commit checks
│   └── pr-verifier.md          # Pre-merge checks
├── commands/               # Slash commands
│   ├── pr-status.md           # /pr-status
│   └── context-recovery.md    # /context-recovery
├── skills/                 # Workflow skills
│   ├── plan-execution/                # Execute plans (agent teams or subagents)
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

### The PR Readiness Check (Why This Matters)

The `/pr-status` command enforces:

1. **CI passes** - Watch all checks to completion
2. **Find the review comment** - Poll until the review bot's comment from the current CI run is found
3. **Read and assess** - Check for CRITICAL, FIX, BLOCKER, DO NOT MERGE
4. **Never report ready without the comment** - The review always posts; wait for it

The review bot posts 10-12 seconds after CI completes. `/pr-status` handles this automatically by polling with timestamp validation. The `plan-execution` skill uses `/pr-status` in a loop: check status, fix if needed, push, re-check until READY TO MERGE.

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
- "Use dev-workflow:plan-execution" - Execute plans with agent teams or subagents (auto-selects based on availability)
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
