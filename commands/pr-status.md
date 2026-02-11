---
description: Watch CI, find the current review comment, scan for blockers, report merge readiness
allowed-tools: Bash(gh:*), Bash(sleep:*), Bash(date:*)
---

# PR Status & Readiness Check

Watches CI to completion, finds and reads the review comment from the current CI run, scans for blockers, and reports whether the PR is ready to merge.

The CI review workflow ALWAYS posts a comment — either with recommended changes or an approval. This command must find that comment before reporting a verdict.

## Step 1: Get PR Info

```bash
gh pr view --json number,title,state,headRefName,url
```

**STOP if no PR exists for this branch.** Create a PR first.

## Step 2: Watch CI to Completion

Check current CI state:

```bash
gh pr checks
```

If any checks are still pending, watch until they complete:

```bash
gh pr checks --watch --fail-fast
```

Report the final CI result:
- **CI PASSED** — proceed to Step 3
- **CI FAILED** — report which checks failed and what needs fixing. Do not continue.

## Step 3: Find the Current Review Comment

The review bot posts after CI completes. Find the comment whose timestamp is newer than the CI workflow completion time.

```bash
PR_NUM=$(gh pr view --json number -q .number)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
CI_COMPLETED=$(gh pr checks --json completedAt -q '.[0].completedAt' 2>/dev/null)

MAX_RETRIES=12
RETRY_COUNT=0
FOUND=0

echo "Waiting for review comment from current CI run..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  COMMENTS=$(gh api "repos/$REPO/issues/$PR_NUM/comments" --jq '.[] | .user.login + "|" + .created_at + "|" + .body' 2>/dev/null)
  REVIEWS=$(gh api "repos/$REPO/pulls/$PR_NUM/reviews" --jq '.[] | select(.body != "") | .user.login + "|" + .submitted_at + "|" + .body' 2>/dev/null)

  ALL_TEXT="$COMMENTS
$REVIEWS"

  if echo "$ALL_TEXT" | grep -iq "claude\|code-review\|github-actions"; then
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
  echo "Attempt $RETRY_COUNT/$MAX_RETRIES — sleeping 5s..."
  sleep 5
done

if [ $FOUND -eq 0 ]; then
  echo "WARNING: No review comment found after 60 seconds."
  echo "The review may still be processing. Try running /pr-status again."
fi
```

## Step 4: Read and Assess the Review Comment

Fetch all comments and reviews for the PR:

```bash
PR_NUM=$(gh pr view --json number -q .number)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "=== PR Comments ==="
gh api "repos/$REPO/issues/$PR_NUM/comments" --jq '.[] | "[\(.user.login)] \(.body)"'

echo ""
echo "=== PR Reviews ==="
gh api "repos/$REPO/pulls/$PR_NUM/reviews" --jq '.[] | select(.body != "") | "[\(.user.login) - \(.state)] \(.body)"'
```

Read every comment carefully. Look for:
- **CRITICAL** / **BLOCKER** / **DO NOT MERGE** — absolute blockers
- **FIX** / **MUST** — should address before merge
- Actionable change requests vs approval/LGTM
- Unresolved questions

## Step 5: Verdict

Report a clear summary:

```
PR #<number> — <title>
Branch: <branch>

CI:       PASSED | FAILED
Review:   FOUND (current) | FOUND (stale) | NOT FOUND
Blockers: NONE | <list of issues to fix>

Verdict:  READY TO MERGE | CHANGES NEEDED — <what to fix>
```

**READY TO MERGE** — CI passed, review comment found from current run, no blocking feedback.

**CHANGES NEEDED** — CI failed, or review comment contains actionable change requests. List exactly what needs to be fixed.

**Never report READY TO MERGE without having found and read the review comment from the current CI run.**
