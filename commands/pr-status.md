---
description: Watch CI, poll for review comment, scan for blockers, report merge readiness
allowed-tools: Bash(gh:*), Bash(sleep:*), Bash(date:*)
---

# PR Status & Readiness Check

Watches CI to completion, polls for the review comment, scans for blockers, and reports whether the PR is ready to merge.

## Step 1: Get PR Info

!`gh pr view --json number,title,state,headRefName,url`

**STOP if no PR exists for this branch.** Use `/pr-create` first.

## Step 2: Watch CI to Completion

Check if CI is already done:

```bash
gh pr checks
```

If any checks are still pending, watch until they complete:

```bash
gh pr checks --watch --fail-fast
```

Report the final CI result:
- **CI PASSED** — proceed to Step 3
- **CI FAILED** — STOP. Report which checks failed. Do not continue.

## Step 3: Poll for Review Comment

Review bots typically post 10-12 seconds after CI passes. Wait for it.

```bash
PR_NUM=$(gh pr view --json number -q .number)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
CI_COMPLETED=$(gh pr checks --json completedAt -q '.[0].completedAt' 2>/dev/null)

MAX_RETRIES=12
RETRY_COUNT=0
FOUND=0

echo "Polling for review comment (up to 60s)..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  COMMENTS=$(gh api "repos/$REPO/issues/$PR_NUM/comments" --jq '.[] | .user.login + "|" + .created_at + "|" + .body' 2>/dev/null)
  REVIEWS=$(gh api "repos/$REPO/pulls/$PR_NUM/reviews" --jq '.[] | select(.body != "") | .user.login + "|" + .submitted_at + "|" + .body' 2>/dev/null)

  ALL_TEXT="$COMMENTS
$REVIEWS"

  if echo "$ALL_TEXT" | grep -iq "claude\|code-review\|github-actions"; then
    # Verify comment is from the current CI run (newer than CI completion)
    if [ -n "$CI_COMPLETED" ]; then
      CI_EPOCH=$(date -d "$CI_COMPLETED" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CI_COMPLETED" +%s 2>/dev/null)
      LATEST_COMMENT_TIME=$(echo "$ALL_TEXT" | grep -i "claude\|code-review\|github-actions" | tail -1 | cut -d'|' -f2)
      COMMENT_EPOCH=$(date -d "$LATEST_COMMENT_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LATEST_COMMENT_TIME" +%s 2>/dev/null)
      if [ -n "$COMMENT_EPOCH" ] && [ -n "$CI_EPOCH" ] && [ "$COMMENT_EPOCH" -ge "$CI_EPOCH" ]; then
        echo "Review comment found (timestamp verified against current CI run)"
        FOUND=1
        break
      else
        echo "Found review comment but it's from a previous CI run — still waiting..."
      fi
    else
      echo "Review comment found"
      FOUND=1
      break
    fi
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT/$MAX_RETRIES — waiting 5s..."
  sleep 5
done

if [ $FOUND -eq 0 ]; then
  echo "WARNING: No review comment found after 60 seconds."
  echo "The review may still be processing, or this repo may not have a review bot configured."
fi
```

## Step 4: Scan for Blockers

Fetch all comments and reviews:

```bash
PR_NUM=$(gh pr view --json number -q .number)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "=== PR Comments ==="
gh api "repos/$REPO/issues/$PR_NUM/comments" --jq '.[] | "[\(.user.login)] \(.body)"'

echo ""
echo "=== PR Reviews ==="
gh api "repos/$REPO/pulls/$PR_NUM/reviews" --jq '.[] | select(.body != "") | "[\(.user.login) - \(.state)] \(.body)"'
```

Read every comment. Look for:
- **CRITICAL** / **BLOCKER** / **DO NOT MERGE** — Absolute blockers
- **FIX** / **MUST** — Should address before merge
- Unresolved questions

## Step 5: Readiness Verdict

Report a clear summary:

```
PR #<number> — <title>
Branch: <branch>

CI:       PASSED | FAILED | PENDING
Review:   FOUND (current) | FOUND (stale) | NOT FOUND
Blockers: NONE | <list>

Verdict:  READY TO MERGE | NOT READY — <reason>
```

Rules for the verdict:
- **READY TO MERGE**: CI passed AND no blocking comments found
- **NOT READY**: CI failed, or CRITICAL/BLOCKER/DO NOT MERGE found

## Next Steps

- If READY: Use `/pr-merge`
- If NOT READY: Fix the issues, push, then run `/pr-status` again
