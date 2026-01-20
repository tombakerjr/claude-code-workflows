# Task Completion Checklist

## Before Completing Any Task

### 1. Syntax Validation

```bash
# Validate all JSON files
python3 -c "import json; json.load(open('hooks/hooks.json'))"
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"

# Validate Python files
python3 -m py_compile hooks/git-guard.py

# Validate Bash files
bash -n hooks/stop-check.sh
bash -n hooks/workflow-preferences.sh
```

### 2. Permissions Check

```bash
# Ensure shell scripts are executable
stat -c "%A %n" hooks/*.sh
# Should show -rwxr-xr-x for all .sh files
```

### 3. Functional Testing

- Test new/modified hooks with simulated input
- Verify exit codes (0 = allow, 2 = block)
- Check JSON output format for hooks with `hookSpecificOutput`

### 4. Version Sync

If releasing a new version:
- `.claude-plugin/plugin.json` version matches
- `.claude-plugin/marketplace.json` version matches

## Code Review

Before merging significant changes, run the `staff-code-reviewer` agent:
- Security review
- Cross-platform compatibility
- Hook configuration correctness
- Documentation accuracy

## Documentation Updates

When adding new features:
- Update README.md with new functionality
- Update hooks table if adding hooks
- Update CLAUDE.md if changing development workflow
- Add mermaid diagrams for complex workflows

## Commit Guidelines

- Use descriptive commit messages
- Include version in commit message for releases (e.g., "v1.1.0: ...")
- Co-author with Claude: `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

## No Build/Test Suite

This plugin has no automated test suite or build process. Validation is manual:
1. Syntax checks (above)
2. Simulated hook testing
3. Installation testing in a separate project
