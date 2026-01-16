---
description: Execute complete PR merge checklist - ALWAYS use this instead of raw gh pr merge
allowed-tools: Bash(gh:*), Bash(sleep:*), Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(tsc:*)
---

# PR Merge Checklist

This command enforces the complete PR merge verification workflow. NEVER skip steps.

## Step 1: Get PR Info

!`gh pr view --json number,title,state,url -q '"\(.number)|\(.title)|\(.state)|\(.url)"'`

Parse and display: PR number, title, state, URL.

## Step 2: Run Type Check

Run your project's typecheck command:

```bash
pnpm run typecheck || npm run typecheck || yarn typecheck || tsc --noEmit
```

**STOP if typecheck fails.** Fix errors before proceeding.

## Step 3: Verify CI Status

!`gh pr checks`

**STOP if any checks are pending or failed.** All must show passed.

## Step 4: Wait for Review Comments

Review comments often post 5-15 seconds AFTER CI completes. This is critical.

!`echo "Waiting 12 seconds for delayed review comments..." && sleep 12`

## Step 5: Fetch ALL Review Comments

```bash
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/issues/$(gh pr view --json number -q .number)/comments --jq '.[] | "\(.user.login): \(.body)"'
```

## Step 6: Analyze Comments

Read EVERY comment above carefully. Check for:

- **CRITICAL** - Absolute blocker, must fix
- **FIX** - Should address before merge
- **BLOCKER** or **DO NOT MERGE** flags
- Unresolved questions or review requests

## Step 7: Decision Point

**IF blockers found:** Report them clearly. DO NOT proceed to merge. Exit this command.

**IF all clear:** Proceed to Step 8.

## Step 8: Execute Merge

!`gh pr merge --squash --delete-branch`

## Step 9: Confirm and Update

!`echo "PR merged successfully"`

After merge:
1. Switch to main and pull: `git checkout main && git pull`
2. Update any feature tracking if applicable
