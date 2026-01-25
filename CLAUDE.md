# CLAUDE.md

This file provides guidance to Claude Code when working with this plugin.

## Overview

This is a Claude Code plugin that enforces PR workflow best practices:
- Pre-commit code verification
- PR merge checklists with delayed comment detection
- Git guardrails (block main push, warn on raw merge)
- Comprehensive code review agents

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
│   ├── pr-create.md           # /pr-create
│   ├── pr-status.md           # /pr-status
│   ├── pr-merge.md            # /pr-merge
│   └── context-recovery.md    # /context-recovery
├── hooks/                  # Event handlers
│   ├── hooks.json             # Hook configuration
│   ├── run-hook.cmd           # Cross-platform wrapper
│   ├── git-guard.py           # PreToolUse: block main push
│   └── stop-check.sh          # Stop: warn on uncommitted
├── CLAUDE.md
└── README.md
```

## Development

### Testing Changes

1. Make changes to plugin files
2. Uninstall if already installed: `/plugin uninstall pr-workflow@pr-workflow-marketplace`
3. Reinstall: `/plugin install pr-workflow@pr-workflow-marketplace`
4. Restart Claude Code for hooks to take effect

### Adding New Components

- **New command**: Create `commands/name.md` with frontmatter
- **New agent**: Create `agents/name.md` with frontmatter
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

### The Merge Checklist (Why This Matters)

The `/pr-merge` command enforces:

1. **Typecheck** - Catch type errors before merge
2. **CI passes** - All checks must show passed
3. **Wait 10-12 seconds** - Review comments post AFTER CI passes
4. **Fetch ALL comments** - Don't miss delayed bot comments
5. **Scan for blockers** - CRITICAL, FIX, BLOCKER, DO NOT MERGE
6. **Only merge when clear** - Human verification required

**Never skip this checklist.** The 10-12 second wait catches review bot comments that post after CI completes.

### Agent Invocation

Agents are invoked automatically based on their descriptions or explicitly:
- "Run the code-verifier agent" - Pre-commit checks
- "Use staff-code-reviewer to review my changes" - Full code review
- "Check if this PR is safe to merge" - PR verification

## Customization

Users should customize:
1. Typecheck commands in `/pr-create` and `/pr-merge`
2. Review criteria in `staff-code-reviewer.md`
3. Blocked patterns in `git-guard.py`

## Compaction Hints

When compacting conversation history, preserve:
- Current task and phase number
- Git branch and last commit SHA
- Any blockers or review feedback not yet addressed
- PR number if one exists

Discard:
- Full file contents (can re-read)
- Verbose build/test output
- Completed task details (just "Task N: complete")

## Token Efficiency

- Clear between unrelated tasks with /clear
- Compact at 50-80% capacity, don't wait for auto-compact at 95%
- Have subagents read files themselves rather than passing content inline
