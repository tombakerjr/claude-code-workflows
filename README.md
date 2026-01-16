# PR Workflow Plugin for Claude Code

A Claude Code plugin that enforces PR workflow best practices through guardrails, verification agents, and workflow commands.

## Features

- **Pre-commit verification** - Type checking, security scans, debug code detection
- **PR merge checklist** - CI verification, delayed comment detection, blocker scanning
- **Git guardrails** - Blocks direct pushes to main, warns on raw merge commands
- **Code review agents** - Staff-level comprehensive reviews
- **Context recovery** - Restore state after context compaction

## Installation

### Option 1: Direct from GitHub (Recommended)

```bash
/plugin marketplace add tombakerjr/claude-code-pr-workflow
/plugin install pr-workflow@claude-code-pr-workflow
```

Then restart Claude Code.

### Option 2: From Local Clone

```bash
git clone https://github.com/tombakerjr/claude-code-pr-workflow.git
/plugin marketplace add /path/to/claude-code-pr-workflow
/plugin install pr-workflow@pr-workflow-marketplace
```

Then restart Claude Code.

## Components

### Slash Commands

| Command | Description |
|---------|-------------|
| `/pr-create` | Verify branch, typecheck, push, create PR with template |
| `/pr-status` | Quick CI + comments + blockers overview |
| `/pr-merge` | **Full merge checklist** - never skip this |
| `/context-recovery` | Recover git/PR state after context compaction |

### Agents

| Agent | Description |
|-------|-------------|
| `staff-code-reviewer` | Comprehensive review: security, correctness, performance, architecture |
| `code-verifier` | Pre-commit: typecheck, security scan, debug code detection |
| `pr-verifier` | Pre-merge: CI status, comment wait, blocker detection |

### Hooks

| Hook | Event | Function |
|------|-------|----------|
| `git-guard.py` | PreToolUse:Bash | Blocks `git push origin main/master`, warns on raw `gh pr merge` |
| `stop-check.sh` | Stop | Warns about uncommitted changes, open PRs, changes on main |

## The Merge Checklist

The `/pr-merge` command enforces this critical workflow:

1. **Typecheck** - Catch type errors before merge
2. **CI passes** - All checks must show passed
3. **Wait 10-12 seconds** - Review comments post AFTER CI passes
4. **Fetch ALL comments** - Don't miss delayed bot comments
5. **Scan for blockers** - CRITICAL, FIX, BLOCKER, DO NOT MERGE
6. **Only merge when clear** - Human verification required

**Why the 10-12 second wait?** Many CI/review bots post their comments several seconds *after* CI completes. Without waiting, you'll miss critical review feedback.

## Usage Examples

### Creating a PR
```
> Create a PR for my changes
# Claude runs /pr-create, which typechecks and creates PR
```

### Checking PR Status
```
> What's the status of my PR?
# Claude runs /pr-status
```

### Merging a PR
```
> Merge my PR
# Claude runs /pr-merge with full checklist
```

### Code Review
```
> Review my recent changes
# Claude invokes staff-code-reviewer agent
```

### Pre-commit Verification
```
> Verify my code before I commit
# Claude invokes code-verifier agent
```

## Customization

### Typecheck Commands

Commands default to trying `pnpm run typecheck || npm run typecheck || yarn typecheck`. Edit the commands to match your project:

- `commands/pr-create.md`
- `commands/pr-merge.md`

### Review Criteria

Add organization-specific review criteria to `agents/staff-code-reviewer.md`:

```markdown
### 6. Organization Standards
- [Your coding standards]
- [Your security requirements]
```

### Additional Git Guards

Add patterns to `hooks/git-guard.py`:

```python
blocked = [
    (r'git\s+push\s+.*\b(main|master)(\s|$)',
     "BLOCKED: Direct push to main/master."),
    # Add your own:
    (r'git\s+push\s+--force',
     "BLOCKED: Force push requires explicit approval."),
]
```

## Requirements

- Claude Code CLI
- `gh` CLI (GitHub CLI) for PR operations
- Git
- For Windows: Git for Windows (provides bash for hooks)

## Recommended Pairing

This plugin works well with the [superpowers](https://github.com/obra/superpowers) plugin:

- `subagent-driven-development` - Main agent coordinates, subagents implement
- `systematic-debugging` - Structured root cause analysis
- `verification-before-completion` - Evidence before success claims
- `receiving-code-review` - Rigorous feedback response

## License

MIT
