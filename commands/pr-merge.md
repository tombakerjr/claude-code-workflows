---
description: Complete PR merge workflow - CI check, comment assessment, fix loop, merge, return to main
allowed-tools: Bash(gh:*), Bash(sleep:*), Bash(git:*), Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(tsc:*)
---

# PR Merge Workflow

Complete merge workflow with CI verification, comment assessment, and fix loop if needed.

## Step 1: Get PR Info

!`gh pr view --json number,title,state,url,headRefName -q '"\(.number)|\(.title)|\(.state)|\(.url)|\(.headRefName)"'`

Parse and display: PR number, title, state, URL, branch name.

## Step 2: Verification

**CI Trust Mode:** Skip local verification if ALL of these are true:
1. CI passed (check in Step 3)
2. CI completed within the last hour
3. No local uncommitted changes

Check CI freshness:
```bash
# Get CI completion time and check if within 1 hour
CI_TIME=$(gh pr checks --json completedAt -q '.[0].completedAt' 2>/dev/null)
if [ -n "$CI_TIME" ]; then
  CI_EPOCH=$(date -d "$CI_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CI_TIME" +%s 2>/dev/null)
  NOW_EPOCH=$(date +%s)
  AGE_MINS=$(( (NOW_EPOCH - CI_EPOCH) / 60 ))
  echo "CI completed $AGE_MINS minutes ago"
  [ $AGE_MINS -lt 60 ] && echo "CI is fresh - can use trust mode" || echo "CI is stale - run local verification"
fi
```

If CI is fresh and `git status` shows clean working tree, skip to Step 3.

Otherwise, run full verification:

```bash
pnpm typecheck && pnpm build && pnpm test
# or equivalent for project
```

**If verification fails:** Fix errors before proceeding. Do not continue.

## Step 3: Check CI Status

!`gh pr checks`

**If checks pending:** Wait and re-check. Do not proceed until all pass.
**If checks failed:** Stop. CI must pass before merge.

## Step 4: Wait for Delayed Comments

Review comments often post 5-15 seconds AFTER CI completes.

!`echo "Waiting 12 seconds for delayed review comments..." && sleep 12`

## Step 5: Fetch All Comments

```bash
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pulls/$(gh pr view --json number -q .number)/comments --jq '.[] | "[\(.user.login)] \(.body)"'
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pulls/$(gh pr view --json number -q .number)/reviews --jq '.[] | select(.body != "") | "[\(.user.login) - \(.state)] \(.body)"'
```

## Step 6: Assess Comments

Read every comment. Look for:
- **CRITICAL** / **BLOCKER** / **DO NOT MERGE** - Absolute blockers
- **FIX** / **MUST** - Should address before merge
- Actionable suggestions vs informational notes
- Unresolved questions

**Categorize:**
- BLOCKING - Must fix
- SUBSTANTIAL - Should fix, will need re-review
- MINOR/OPTIONAL - Can merge, address later if desired
- INFORMATIONAL - No action needed

## Step 7: Decision Point

### If BLOCKING or SUBSTANTIAL Issues Found:

```
Issues found that need addressing:

BLOCKING:
- [issue description]

SUBSTANTIAL:
- [issue description]

Implementing fixes...
```

1. Dispatch implementer to fix issues
2. Run verification (Step 2)
3. Commit fixes: `fix: address PR review feedback`
4. Push to PR branch
5. Run staff-code-reviewer on the fixes
6. **Loop back to Step 3** (re-check CI, wait for new comments)

Max 2 fix loops. If still blocked after 2 attempts, escalate to user.

### If All Clear (only MINOR or INFORMATIONAL):

Proceed to Step 8.

## Step 8: Merge

Check project conventions for merge strategy. Default to squash:

```bash
gh pr merge --squash --delete-branch
```

If project prefers different strategy (check CLAUDE.md or repo settings):
- `--merge` for merge commit
- `--rebase` for rebase

## Step 9: Return to Main

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
