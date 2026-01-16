---
description: Quick PR status check - CI, comments, blockers
allowed-tools: Bash(gh:*)
---

# PR Status Check

Quick overview of current PR status.

## Current PR

!`gh pr view --json number,title,state,headRefName,url`

## CI Status

!`gh pr checks`

## Recent Comments

Fetch all PR comments:

```bash
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/issues/$(gh pr view --json number -q .number)/comments --jq '.[] | "\(.user.login): \(.body)"'
```

## Summary

Report:
1. PR number and branch
2. CI status: PASSED / FAILED / PENDING
3. Comment count
4. Any blockers detected (CRITICAL, FIX, BLOCKER keywords)

## Next Steps

- If CI pending: Wait and check again
- If CI failed: Fix issues and push
- If CI passed with no blockers: Use `/pr-merge`
- If blockers found: Address them first
