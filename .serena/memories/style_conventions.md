# Style and Conventions

## Python (hooks/*.py)

- **Python version**: 3.x (use modern features like f-strings, type hints optional)
- **Imports**: Standard library only (no external dependencies)
- **Docstrings**: Module-level docstring explaining purpose and usage
- **Functions**: Short docstrings for non-trivial functions
- **Error handling**: Catch specific exceptions, fail gracefully (exit 0 on unexpected errors)
- **Output**: 
  - Use `sys.stderr` for error/block messages
  - Use `print(json.dumps(...))` for hook output with `hookSpecificOutput`
  - Exit codes: 0 = allow, 2 = block

Example structure:
```python
#!/usr/bin/env python3
"""
Module docstring explaining purpose.
"""
import json
import sys

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)  # Fail open
    
    # ... logic ...
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Bash (hooks/*.sh)

- **Shebang**: `#!/bin/bash`
- **Comments**: Brief header comment explaining purpose
- **Output**: Use heredoc for JSON output to avoid escaping issues
- **Permissions**: Must be executable (`chmod +x`)

Example structure:
```bash
#!/bin/bash
# Brief description of what this hook does

cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "EventName",
    "additionalContext": "Context string with \\n for newlines"
  }
}
EOF
```

## Markdown (agents/*.md, commands/*.md)

- **Frontmatter**: YAML with `name` and `description` fields
- **Structure**: Clear sections with headers
- **Instructions**: Imperative voice, specific and actionable

Example:
```markdown
---
name: agent-name
description: Brief description for invocation matching
---

# Agent Name

## Purpose
What this agent does.

## Steps
1. First step
2. Second step
```

## JSON Configuration

- **Indentation**: 2 spaces
- **Paths**: Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- **Hooks**: Use `run-hook.cmd` wrapper for cross-platform compatibility

## Cross-Platform Considerations

- Shell scripts work via `run-hook.cmd` polyglot wrapper
- Python scripts use cross-platform `subprocess` module
- Avoid Unix-specific commands in hook scripts
- Test on Windows (Git Bash), macOS, and Linux
