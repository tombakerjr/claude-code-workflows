# Suggested Commands

## Development Commands

### Testing Plugin Changes

```bash
# Validate JSON syntax
python3 -c "import json; json.load(open('hooks/hooks.json'))"
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"

# Validate Python syntax
python3 -m py_compile hooks/git-guard.py

# Validate Bash syntax
bash -n hooks/stop-check.sh
bash -n hooks/workflow-preferences.sh

# Test git-guard.py with simulated input
echo '{"tool_name": "Bash", "tool_input": {"command": "git commit -m test"}}' | python3 hooks/git-guard.py
```

### Plugin Installation (for testing in another project)

```bash
# Uninstall existing version
/plugin uninstall pr-workflow@pr-workflow-marketplace

# Reinstall from local path
/plugin marketplace add /path/to/claude-code-workflows
/plugin install pr-workflow@pr-workflow-marketplace

# Restart Claude Code for hooks to take effect
```

### Version Bump

When releasing a new version:
1. Update `version` in `.claude-plugin/plugin.json`
2. Update `version` in `.claude-plugin/marketplace.json`
3. Commit changes
4. Tag: `git tag v1.x.x`
5. Push: `git push && git push --tags`

## System Utilities (Linux)

```bash
# File operations
ls -la                    # List files with details
find . -name "*.py"       # Find files by pattern
grep -r "pattern" .       # Search in files

# Git operations
git status                # Check working tree
git diff                  # Show unstaged changes
git log --oneline -5      # Recent commits
git branch -a             # List branches

# File permissions (important for hooks)
chmod +x hooks/*.sh       # Make shell scripts executable
stat -c "%A %n" hooks/*   # Check permissions
```

## Hook Testing

```bash
# Test git-guard.py commit blocking (must be on main branch)
python3 -c "
import subprocess
result = subprocess.run(
    ['python3', 'hooks/git-guard.py'],
    input='{\"tool_name\": \"Bash\", \"tool_input\": {\"command\": \"git commit -m test\"}}',
    capture_output=True, text=True
)
print(f'Exit code: {result.returncode}')
print(f'Stderr: {result.stderr[:200]}')
"

# Test workflow-preferences.sh output
bash hooks/workflow-preferences.sh | python3 -c "import json,sys; print(json.load(sys.stdin))"
```
