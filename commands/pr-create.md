---
description: Create PR with typecheck verification and proper formatting
allowed-tools: Bash(git:*), Bash(gh:*), Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(tsc:*)
---

# Create Pull Request

This command creates a PR after verifying code quality.

## Step 1: Verify Branch

!`git branch --show-current`

**STOP if on main/master.** Create a feature branch first.

## Step 2: Run Type Check

Run your project's typecheck command. Try these in order until one works:

```bash
pnpm run typecheck || npm run typecheck || yarn typecheck || tsc --noEmit
```

**STOP if typecheck fails.** Fix all errors before creating PR.

## Step 3: Check for Uncommitted Changes

!`git status --short`

If there are uncommitted changes, commit them first with proper attribution.

## Step 4: Push Branch

Push the current branch to origin:

```bash
git push -u origin $(git branch --show-current)
```

## Step 5: Create PR

Construct PR with:
- Title: Brief description of changes
- Body: Summary, testing notes, attribution

Format:
```markdown
## Summary
- Change 1
- Change 2

## Testing
- [ ] Type check passes
- [ ] Manual testing completed

## Notes
<Any additional context>

---
Generated with [Claude Code](https://claude.ai/claude-code)
```

Create the PR:
```bash
gh pr create --title "TITLE" --body "BODY"
```

## Step 6: Confirm

!`gh pr view --json number,url -q '"PR #\(.number): \(.url)"'`

## Next Steps

- Wait for CI to complete
- Use `/pr-status` to check CI and comments
- Use `/pr-merge` when ready to merge
