---
description: >
  Use PROACTIVELY when context feels incomplete, after compaction, or when unsure about
  current git/PR state. Run this when resuming work, after /clear, or when confused about
  project status. Recovers git state, open PRs, and workflow reminders.
allowed-tools: Bash(git:*), Bash(gh:*), Read
---

# Context Recovery

Run this if context feels incomplete or after compaction.

## Quick Recovery (Default)

!`git branch --show-current && git status -s && gh pr view --json number,state,title 2>/dev/null || echo "No PR"`

If this is sufficient, stop here. Otherwise continue to Full Recovery.

## Full Recovery

## Step 1: Git State

!`git branch --show-current && echo "---" && git status --short && echo "---" && git log --oneline -5`

## Step 2: Open PR Status

!`gh pr view --json number,title,state,headRefName 2>/dev/null || echo "No open PR on this branch"`

## Step 3: Recent Activity

!`git log --oneline -10 --all`

## Step 4: Read Project Documentation

If there's a CLAUDE.md, read it for project-specific workflow rules.

## Step 5: Critical Workflow Reminders

**CRITICAL WORKFLOWS - NEVER SKIP:**

1. **All changes through PRs** - Never push directly to main
2. **Before merge, verify inline (no dedicated slash command):**
   - `gh pr checks <pr> --watch` - CI must pass
   - Parse `**Reviewed commit:** <short-sha>` from the latest `claude[bot]`
     sticky comment; compare to `gh pr view <pr> --json headRefOid -q .headRefOid`
   - Mismatch / missing / null -> retry up to 3x with 5s backoff, then wait
     for the next CI run
   - Scan the matched comment for CRITICAL / FIX / BLOCKER markers

## Step 6: Summary

Report current state:
1. Current branch
2. Uncommitted changes (if any)
3. Open PR status (if any)
4. Recent commits
5. Next recommended action
