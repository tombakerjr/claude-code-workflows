---
description: Complete PR merge workflow - readiness check via /pr-status, local verification, fix loop, merge, return to main
allowed-tools: Bash(gh:*), Bash(sleep:*), Bash(git:*), Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(tsc:*)
---

# PR Merge Workflow

Complete merge workflow: readiness check, local verification, fix loop if needed, merge, return to main.

## Step 1: Readiness Check

Run `/pr-status` to watch CI, poll for the review comment, and scan for blockers.

**STOP if the verdict is NOT READY.** Fix the reported issues first.

Record the PR number, branch, and URL from the status output for use in later steps.

## Step 2: Local Verification

**CI Trust Mode:** Skip local verification if ALL of these are true:
1. `/pr-status` reported CI PASSED
2. CI completed within the last hour
3. No local uncommitted changes (`git status` shows clean working tree)

Check CI freshness:
```bash
CI_TIME=$(gh pr checks --json completedAt -q '.[0].completedAt' 2>/dev/null)
if [ -n "$CI_TIME" ]; then
  CI_EPOCH=$(date -d "$CI_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CI_TIME" +%s 2>/dev/null)
  if [ -n "$CI_EPOCH" ]; then
    NOW_EPOCH=$(date +%s)
    AGE_MINS=$(( (NOW_EPOCH - CI_EPOCH) / 60 ))
    echo "CI completed $AGE_MINS minutes ago"
    [ $AGE_MINS -lt 60 ] && echo "CI is fresh — can use trust mode" || echo "CI is stale — run local verification"
  else
    echo "Unable to parse CI completion time — running local verification"
  fi
fi
```

If CI is stale or working tree is dirty, run full verification:

```bash
pnpm typecheck && pnpm build && pnpm test
# or equivalent for project
```

**If verification fails:** Fix errors before proceeding. Do not continue.

## Step 3: Assess Review Feedback

Using the comments fetched by `/pr-status`, categorize each piece of feedback:

- **BLOCKING** — Must fix (CRITICAL, BLOCKER, DO NOT MERGE)
- **SUBSTANTIAL** — Should fix, will need re-review
- **MINOR/OPTIONAL** — Can merge, address later if desired
- **INFORMATIONAL** — No action needed

### If BLOCKING or SUBSTANTIAL Issues Found:

```
Issues found that need addressing:

BLOCKING:
- [issue description]

SUBSTANTIAL:
- [issue description]

Implementing fixes...
```

1. Fix the issues
2. Run local verification (Step 2)
3. Commit fixes: `fix: address PR review feedback`
4. Push to PR branch
5. Run staff-code-reviewer on the fixes
6. **Loop back to Step 1** — run `/pr-status` again to re-check CI and new comments

Max 2 fix loops. If still blocked after 2 attempts, escalate to user.

### If All Clear (only MINOR or INFORMATIONAL):

Proceed to Step 4.

## Step 4: Merge

Check project conventions for merge strategy. Default to squash:

```bash
gh pr merge --squash --delete-branch
```

If project prefers different strategy (check CLAUDE.md or repo settings):
- `--merge` for merge commit
- `--rebase` for rebase

## Step 5: Return to Main

```bash
git checkout main
git pull origin main
```

Report:
```
PR #<number> merged successfully
Branch: <branch-name> (deleted)
Now on: main (up to date with origin)
```
