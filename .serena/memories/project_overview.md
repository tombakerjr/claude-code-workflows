# PR Workflow Plugin for Claude Code

## Purpose

A Claude Code plugin that enforces PR workflow best practices through:
- Git guardrails (blocks commits/pushes to main, warns on raw merge)
- Pre-commit verification agents
- PR merge checklists with delayed comment detection
- Staff-level code review agents
- SessionStart execution preference injection

## Tech Stack

| Component | Technology |
|-----------|------------|
| Hooks | Python 3 (`git-guard.py`), Bash (`stop-check.sh`, `workflow-preferences.sh`) |
| Config | JSON (`plugin.json`, `marketplace.json`, `hooks.json`) |
| Agents/Commands | Markdown with YAML frontmatter |
| Cross-platform wrapper | Batch/Bash polyglot (`run-hook.cmd`) |

## Project Structure

```
claude-code-workflows/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata and version
│   └── marketplace.json     # For direct installation
├── agents/                   # Subagent definitions
│   ├── staff-code-reviewer.md
│   ├── code-verifier.md
│   └── pr-verifier.md
├── commands/                 # Slash commands
│   ├── pr-create.md
│   ├── pr-status.md
│   ├── pr-merge.md
│   └── context-recovery.md
├── hooks/                    # Event handlers
│   ├── hooks.json            # Hook configuration
│   ├── run-hook.cmd          # Cross-platform wrapper
│   ├── git-guard.py          # PreToolUse: blocks main commits/pushes
│   ├── stop-check.sh         # Stop: warns on uncommitted changes
│   └── workflow-preferences.sh # SessionStart: execution preferences
├── CLAUDE.md                 # Development instructions
└── README.md                 # User documentation
```

## Key Files

- **Version**: Defined in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (must be kept in sync)
- **Hook registration**: `hooks/hooks.json` defines which scripts run on which events
- **Git guards**: `hooks/git-guard.py` is the main enforcement script

## Current Version

v1.1.0
