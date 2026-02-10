---
name: agent-team-development
description: Use when executing implementation plans with parallel agent teams (falls back to subagent-driven-development if agent teams not enabled)
---

# Agent Team Development

Execute plans with parallel agent teams: multiple implementers in git worktrees, a dedicated reviewer, and a lead coordinator. Falls back to subagent-driven-development when agent teams aren't available.

**Core principle:** True parallel execution with bidirectional communication via mailbox.

## When to Use

- Have an implementation plan with tasks and recommended models
- Tasks are parallelizable (multiple can run simultaneously)
- Want true parallel execution across worktrees
- Agent teams enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var set)

**Automatic fallback:** If the env var is not set, invoke `dev-workflow:subagent-driven-development` instead.

## Fallback Check

Before anything else:

```bash
if [ -z "$CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ]; then
  # Agent teams not enabled - fall back
  # Invoke: dev-workflow:subagent-driven-development
fi
```

If the env var is not set, immediately invoke `dev-workflow:subagent-driven-development` with the same plan. Do not proceed with team setup.

## Team Structure

| Role | Count | Model | Responsibility |
|------|-------|-------|----------------|
| **Lead (you)** | 1 | opus | Orchestration-only (delegate mode). Reads plan, creates shared tasks, monitors progress, performs phase/final reviews. |
| **Implementers** | 2-3 | sonnet (or per plan) | Each in own git worktree. Self-claim tasks from shared task list. Pull latest before each task. Commit to shared feature branch. |
| **Reviewer** | 1 | sonnet | Persistent teammate. Watches for completed implementation tasks. Reviews and sends feedback directly to implementers via mailbox. |

**Implementer count:**
- 2 implementers for plans with ≤4 tasks
- 3 implementers for plans with 5+ tasks

## Task Classification

Classify each task before creating shared tasks:

| Complexity | Impl Model | Review Path | Indicators |
|------------|------------|-------------|------------|
| SIMPLE | haiku (if plan says) | quick-reviewer only | ≤2 files, config, boilerplate, mechanical |
| STANDARD | sonnet (default) | spec + quality review | Multi-file, business logic, error handling |
| COMPLEX | sonnet or opus | spec + quality + extra scrutiny | Only if plan explicitly requires |

## The Complete Flow

```
FALLBACK CHECK
======================================================================
1. Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var
   If NOT set → invoke dev-workflow:subagent-driven-development instead
   If set → continue with team setup

SETUP
======================================================================
2. Ensure on feature branch (create if needed)
3. Read plan, extract ALL tasks with:
   - Full task text
   - Recommended model (default: sonnet)
   - Complexity classification (SIMPLE/STANDARD/COMPLEX)
   - Dependencies between tasks
   - Parallelizable: yes/no
4. Determine implementer count (2 for ≤4 tasks, 3 for 5+)

WORKTREE SETUP
======================================================================
5. Create git worktrees for each implementer:
   Pattern: .worktrees/team-BRANCH-impl-N

   Example for branch "feature/auth":
     .worktrees/team-feature-auth-impl-1
     .worktrees/team-feature-auth-impl-2
     .worktrees/team-feature-auth-impl-3

   Commands:
     git worktree add .worktrees/team-feature-auth-impl-1 HEAD
     git worktree add .worktrees/team-feature-auth-impl-2 HEAD
     ...

   Ensure `.worktrees/` is in `.gitignore`.

DELEGATE MODE
======================================================================
6. Enter delegate mode (Shift+Tab)
   Lead becomes orchestration-only from this point.

SPAWN TEAMMATES
======================================================================
7. Spawn implementer teammates (one per worktree)
8. Spawn reviewer teammate

CREATE SHARED TASKS
======================================================================
9. Create shared tasks from plan (all phases or current phase)
   Each task includes:
   - Task title from plan
   - Full description with acceptance criteria
   - Complexity classification
   - Model recommendation
   - Phase number

EXECUTION
======================================================================
10. Implementers self-claim tasks from shared task list
11. Each implementer:
    a. Pull latest from feature branch
    b. Implement the task in their worktree
    c. Run tests and self-verify
    d. Commit to feature branch
    e. Push to remote
    f. Mark task ready for review

12. Reviewer watches for ready-for-review tasks:
    SIMPLE tasks:
      - Quick review (spec + quality combined)
      - Send PASS/FAIL via mailbox to implementer

    STANDARD+ tasks:
      - Spec review (does it match acceptance criteria?)
      - Quality review (code quality, patterns, tests)
      - Send PASS/FAIL via mailbox to implementer

13. Fix loops (via mailbox):
    - Reviewer sends feedback directly to implementer
    - Implementer fixes, re-commits, re-pushes
    - Reviewer re-reviews
    - Max 3 attempts, then escalate to lead

PHASE BOUNDARY
======================================================================
14. Wait for all tasks in phase to complete + pass review
15. Skip phase review if ALL tasks in phase were SIMPLE
16. Otherwise: Lead performs staff-code-reviewer on phase commits
    Commits: [phase_start_sha]..[current_sha]

    If CRITICAL/IMPORTANT issues:
      → Assign fix to an implementer via shared task
      → Re-verify after fix
      → Re-run staff-code-reviewer (max 2 attempts)

FINAL
======================================================================
17. Lead performs final staff-code-reviewer (opus) on entire implementation
18. Clean up worktrees:
    git worktree remove .worktrees/team-BRANCH-impl-1
    git worktree remove .worktrees/team-BRANCH-impl-2
    ...
    git worktree prune
19. Create PR (follow repo template if exists)
20. Invoke /pr-merge workflow (or user invokes manually)
```

## Spawn Prompt Templates

### Implementer Spawn Prompt

```
You are an implementer on an agent team. Your role is to pick up tasks
from the shared task list, implement them, and commit your work.

## Your Worktree
Working directory: [WORKTREE_PATH]
Feature branch: [BRANCH_NAME]

IMPORTANT: cd into your worktree directory and work from there.
All git and file operations should happen from within the worktree.
Only fall back to `git -C` if you cannot cd into the worktree.

## Workflow
1. cd into your worktree: cd [WORKTREE_PATH]
2. Check the shared task list for unclaimed tasks
3. Claim a task by marking it in_progress
4. Before starting: git pull to get latest changes
5. Implement the task following its acceptance criteria
6. Run tests and verify your changes
7. Commit with conventional message: feat|fix|refactor: description
8. Push to remote: git push
9. Mark the task as ready for review (add "READY FOR REVIEW" to task)
10. Wait for reviewer feedback via mailbox
11. If reviewer requests fixes: fix, commit, push, notify reviewer
12. Once approved: move to next task

## Guidelines
- Work from within your worktree directory (cd into it first)
- Follow project conventions from CLAUDE.md
- Write tests as specified in the task's testing approach
- Keep commits focused on the task
- Pull before each new task to avoid conflicts
- If blocked or confused, message the lead for guidance
- Use the model recommended in the task (haiku for SIMPLE, sonnet for STANDARD)

## Task Claiming
- Only claim tasks that are not blocked by incomplete dependencies
- Prefer tasks in the current phase
- If all remaining tasks have dependencies, wait or ask lead
```

### Reviewer Spawn Prompt

```
You are the reviewer on an agent team. Your role is to review completed
implementation tasks and provide feedback directly to implementers.

## Workflow
1. Watch the shared task list for tasks marked "READY FOR REVIEW"
2. For each ready task:

   SIMPLE tasks (≤2 files, config, boilerplate):
   - Quick combined spec + quality review
   - Check: Does it match acceptance criteria?
   - Check: Code quality acceptable?
   - Send PASS or feedback via mailbox to the implementer

   STANDARD+ tasks:
   - Spec review: Does implementation match acceptance criteria exactly?
   - Quality review: Code quality, patterns, test coverage, error handling
   - Send PASS or detailed feedback via mailbox to the implementer

3. If you send feedback (FAIL):
   - Be specific: file, line, issue, suggested fix
   - Use structured format:
     ## Review Feedback (Attempt N of 3)
     Status: [spec_failure|quality_failure]
     File: path/to/file
     Issues:
     1. Line N: [issue] -> [fix]
   - Wait for implementer to fix and re-submit
   - Re-review the fixes
   - Max 3 review rounds per task

4. If fixes fail after 3 attempts:
   - Message the lead with escalation details
   - Include: task name, issue description, what was tried

## Review Standards
- Match acceptance criteria exactly (spec)
- No security vulnerabilities (quality)
- Tests present and meaningful (quality)
- Follows project patterns from CLAUDE.md (quality)
- No over-engineering or scope creep (quality)

## Communication
- Use mailbox to communicate with implementers
- Be concise but specific in feedback
- Acknowledge good work on PASS
```

## Fix Loop Severity

Classify fix complexity (same as subagent-driven-development):

| Fix Type | Model | Max Attempts | Indicators |
|----------|-------|--------------|------------|
| MINOR | haiku (override) | 2 | Typo, missing import, lint fix |
| STANDARD | sonnet | 2 | Logic error, error handling, test fix |
| COMPLEX | sonnet -> opus (with approval) | 2 + escalate | Architectural feedback, multi-file fix |

## Escalation

**Escalate to user (lead asks) when:**
- Fix loop exceeds max attempts (3 task-level, 2 phase-level)
- Reviewer and implementer disagree after 3 rounds
- Security concern needs judgment
- Architectural decision needed
- Merge conflicts between worktrees that can't be auto-resolved

```
ESCALATION NEEDED

Task: [N name]
Issue: [what's blocking]
Attempts: [N of max]
Last feedback: [reviewer's comment]

Options:
1. [suggested approach]
2. [alternative]
3. Skip and document as known issue
```

## Worktree Management

### Creation (during setup)

```bash
# Get branch name for worktree naming
BRANCH_NAME=$(git branch --show-current | tr '/' '-')

# Create worktrees inside .worktrees/
git worktree add ".worktrees/team-${BRANCH_NAME}-impl-1" HEAD
git worktree add ".worktrees/team-${BRANCH_NAME}-impl-2" HEAD
# Add impl-3 if 5+ tasks

# Ensure .worktrees/ is in .gitignore
```

### Cleanup (during final)

```bash
git worktree remove ".worktrees/team-${BRANCH_NAME}-impl-1"
git worktree remove ".worktrees/team-${BRANCH_NAME}-impl-2"
# Remove impl-3 if it exists
git worktree prune
```

### Conflict Prevention

- Each implementer pulls before starting a new task
- Tasks should be designed to minimize file overlap
- If conflicts arise: implementer pulls, resolves, recommits
- Lead can reassign conflicting tasks to a single implementer

## Red Flags

**Never:**
- Skip the fallback check
- Skip verification after fixes
- Let fix loops run indefinitely
- Proceed with CRITICAL issues from phase review
- Use opus for every implementation task
- Leave worktrees behind after completion

**Always:**
- Check for agent teams env var before proceeding
- Enter delegate mode before spawning teammates
- Classify task complexity before creating shared tasks
- Use structured feedback format for reviews
- Clean up worktrees during final step
- Track review attempts per task
- Escalate when stuck

## Model Selection

| Role | Default Model | Override |
|------|---------------|---------|
| Lead (orchestration) | opus | - |
| Implementer (standard) | sonnet | haiku if plan says |
| Implementer (simple) | sonnet | haiku if plan says |
| Reviewer | sonnet | - |
| Staff reviewer (phase/final) | opus | - |

## Integration

**Uses:**
- Shared task list (agent teams feature) for work coordination
- Mailbox (agent teams feature) for reviewer <-> implementer communication
- Git worktrees for workspace isolation
- `dev-workflow:staff-code-reviewer` - phase/final reviews (run by lead)
- `/pr-merge` command - CI check, comment assessment, merge

**Falls back to:**
- `dev-workflow:subagent-driven-development` - when agent teams not enabled

**Works with:**
- `dev-workflow:writing-plans` - creates plans with model recommendations and parallelizable field
- `dev-workflow:brainstorming` - design exploration before planning
- `dev-workflow:systematic-debugging` - bug investigation workflow
- `dev-workflow:test-driven-development` - TDD discipline for implementation
