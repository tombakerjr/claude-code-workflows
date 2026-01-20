# PR Workflow Plugin for Claude Code

A Claude Code plugin that enforces PR workflow best practices through guardrails, verification agents, and workflow commands.

## Features

- **Pre-commit verification** - Type checking, security scans, debug code detection
- **PR merge checklist** - CI verification, delayed comment detection, blocker scanning
- **Git guardrails** - Blocks direct pushes to main, warns on raw merge commands
- **Code review agents** - Staff-level comprehensive reviews
- **Context recovery** - Restore state after context compaction
- **Execution preferences** - Enforces subagent-driven-development for plan execution

## Feature Development Workflow

This plugin enforces a structured workflow for feature development. The diagram below shows the complete lifecycle from starting work to merging.

```mermaid
flowchart TD
    subgraph START ["Start Feature Work"]
        A[New task/feature request] --> B{On main branch?}
        B -->|Yes| C[Create feature branch]
        B -->|No| D[Use current branch]
        C --> E[git checkout -b feature/name]
        E --> F[Ready to develop]
        D --> F
    end

    subgraph DEV ["Development Iteration"]
        F --> G[Write code]
        G --> H[Run code-verifier agent]
        H --> I{Verification passed?}
        I -->|No| J[Fix issues]
        J --> G
        I -->|Yes| K[Commit changes]
        K --> L{More work needed?}
        L -->|Yes| G
        L -->|No| M[Ready for PR]
    end

    subgraph PR ["Pull Request"]
        M --> N[/pr-create]
        N --> O[Typecheck + Push + Create PR]
        O --> P[Wait for CI]
        P --> Q[Request review / Run staff-code-reviewer]
    end

    subgraph REVIEW ["Review Iteration"]
        Q --> R{Review feedback?}
        R -->|Changes requested| S[Address feedback]
        S --> T[Commit fixes]
        T --> U[Push updates]
        U --> P
        R -->|Approved| V[Ready to merge]
    end

    subgraph MERGE ["Safe Merge"]
        V --> W[/pr-merge]
        W --> X[Typecheck]
        X --> Y[Verify CI passed]
        Y --> Z[Wait 10-12 seconds]
        Z --> AA[Fetch ALL comments]
        AA --> AB{Blockers found?}
        AB -->|Yes| AC[Address blockers]
        AC --> T
        AB -->|No| AD[Merge PR]
        AD --> AE[Delete branch]
        AE --> AF[Done!]
    end

    style START fill:#e1f5fe
    style DEV fill:#fff3e0
    style PR fill:#f3e5f5
    style REVIEW fill:#e8f5e9
    style MERGE fill:#fce4ec
```

### Workflow Phases

| Phase | Key Actions | Plugin Support |
|-------|-------------|----------------|
| **Start** | Create feature branch, never commit to main | `git-guard.py` blocks commits on main |
| **Develop** | Write code, verify before commits | `code-verifier` agent, iterative fixes |
| **PR Creation** | Typecheck, push, create PR | `/pr-create` command |
| **Review** | Get feedback, iterate on changes | `staff-code-reviewer` agent |
| **Merge** | Full checklist before merge | `/pr-merge` with 10-12s wait for delayed comments |

### Git Guards

The plugin prevents common mistakes:

| Action | On Main | On Feature Branch |
|--------|---------|-------------------|
| `git commit` | Blocked | Allowed |
| `git push origin main` | Blocked | N/A |
| `gh pr merge` | Warned (use /pr-merge) | Warned (use /pr-merge) |

### Execution Preference

When executing implementation plans (from `writing-plans` or similar), this plugin enforces:

- **Use**: `superpowers:subagent-driven-development`
- **Not**: `superpowers:executing-plans`

Subagent-driven development keeps work in the current session with fresh context per task, avoiding context bloat from long-running executions.

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
| `git-guard.py` | PreToolUse:Bash | Blocks commits on main/master, blocks push to main/master, warns on raw `gh pr merge` |
| `stop-check.sh` | Stop | Warns about uncommitted changes, open PRs, changes on main |
| `workflow-preferences.sh` | SessionStart | Injects execution preferences (use subagent-driven-development) |

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
