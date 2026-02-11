---
name: plan-execution
description: Use when executing implementation plans. Selects between agent teams (parallel teammates in worktrees) and subagents (parallel Task tool dispatch) based on availability.
---

# Plan Execution

Execute implementation plans with parallel workers. Automatically selects between **team mode** (agent teams with worktrees) and **subagent mode** (Task tool with `run_in_background`).

**Core principle:** Implement -> Verify -> Review -> Fix (if needed) -> Loop until pass

## Mode Selection

```bash
if [ -z "$CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ]; then
  # → Subagent mode
else
  # → Team mode
fi
```

### Mode Tradeoffs

| | Team Mode | Subagent Mode |
|---|---|---|
| Parallelism | Worktrees + spawned teammates | `run_in_background` on Task tool |
| Communication | Bidirectional mailbox | None — orchestrator relays all feedback |
| Context | Teammates inherit lead's full context | Subagents only see what you pass them (lightweight) |
| Model control | Teammates inherit lead's model | Each subagent gets its own `model` param |
| Best for | Complex, interdependent tasks needing direct communication | Well-scoped, independent tasks |

**Subagent mode is more efficient for simpler tasks** — subagents start with only the prompt you give them, avoiding the overhead of loading the full conversation context. Use team mode when tasks are tightly coupled and benefit from shared context and direct reviewer-implementer communication.

## Task Classification

Classify each task before execution:

| Complexity | Impl Model | Review Path | Indicators |
|------------|------------|-------------|------------|
| SIMPLE | haiku (if plan says) | quick-reviewer only | ≤2 files, config, boilerplate, mechanical |
| STANDARD | sonnet (default) | spec + quality review | Multi-file, business logic, error handling |
| COMPLEX | sonnet or opus | spec + quality + extra scrutiny | Only if plan explicitly requires |

## Model Selection

| Role | Default Model | Notes |
|------|---------------|-------|
| Lead (orchestration) | opus | — |
| Implementer (standard) | sonnet | Team mode: inherits lead's model. Subagent mode: pass `model` param. |
| Implementer (simple) | sonnet | Override to haiku if plan recommends |
| Quick reviewer | haiku | Subagent mode only |
| Spec reviewer | sonnet | Subagent mode only |
| Quality reviewer | sonnet | Subagent mode only |
| Reviewer teammate | inherits lead | Team mode only |
| Staff reviewer (phase/final) | opus | Both modes |

## The Complete Flow

```
SETUP
======================================================================
1. Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS → select mode
2. Ensure on feature branch (create if needed)
3. Read plan, extract ALL tasks with:
   - Full task text
   - Recommended model (default: sonnet)
   - Complexity classification (SIMPLE/STANDARD/COMPLEX)
   - Dependencies between tasks
   - Parallelizable: yes/no

TEAM MODE SETUP (skip if subagent mode)
======================================================================
4. Determine implementer count (2 for ≤4 tasks, 3 for 5+)
5. Create git worktrees for each implementer:
   Pattern: .worktrees/team-BRANCH-impl-N
   Ensure `.worktrees/` is in `.gitignore`
6. Enter delegate mode (Shift+Tab)
7. Spawn implementer teammates (one per worktree)
8. Spawn reviewer teammate
9. Create shared tasks from plan

SUBAGENT MODE SETUP (skip if team mode)
======================================================================
4. Create TodoWrite with all tasks

EXECUTION
======================================================================

Team mode:
  Implementers self-claim tasks from shared task list.
  Each implementer: pull → implement → test → commit → push → mark ready
  Reviewer watches for ready tasks:
    SIMPLE: quick combined review → PASS/FAIL via mailbox
    STANDARD+: spec + quality review → PASS/FAIL via mailbox
  Fix loops via mailbox (max 3 rounds, then escalate to lead)

Subagent mode:
  For each task (parallel where independent via run_in_background):
    a. Mark task in_progress in TodoWrite
    b. Dispatch implementer subagent (model from plan)
    c. Run verification (typecheck, build, tests)
       If FAILS → dispatch implementer with error output (max 3 attempts)
    d. Review:
       SIMPLE: dispatch quick-reviewer (haiku) — single pass
       STANDARD+: dispatch spec-reviewer then quality-reviewer (sonnet)
       If ISSUES → dispatch implementer with feedback (max 3 attempts)
    e. Mark task completed

PHASE BOUNDARY
======================================================================
Wait for all tasks in phase to complete + pass review.
Skip phase review if ALL tasks in phase were SIMPLE.
Otherwise: staff-code-reviewer (opus) on phase commits
  Commits: [phase_start_sha]..[current_sha]

  If CRITICAL/IMPORTANT:
    → Assign fix (shared task or subagent dispatch)
    → Re-verify after fix
    → Re-run staff-code-reviewer (max 2 attempts)

FINAL
======================================================================
[Team mode] Clean up worktrees:
  git worktree remove .worktrees/team-BRANCH-impl-N
  git worktree prune

Final staff-code-reviewer (opus) on entire implementation.

Push and create PR.
Run /pr-status to watch CI and find the review comment.
If CHANGES NEEDED:
  a. Fix the issues reported in the review comment
  b. Optionally run staff-code-reviewer on the fixes (agent's judgment)
  c. Commit and push
  d. Re-run /pr-status
If READY TO MERGE:
  a. Merge if user authorized, or report ready and wait for user
```

---

## Team Mode Details

### Team Structure

| Role | Count | Responsibility |
|------|-------|----------------|
| **Lead (you)** | 1 | Orchestration-only (delegate mode). Reads plan, creates shared tasks, monitors progress, performs phase/final reviews. |
| **Implementers** | 2-3 | Each in own git worktree. Self-claim tasks from shared task list. Pull latest before each task. Commit to shared feature branch. |
| **Reviewer** | 1 | Persistent teammate. Watches for completed tasks. Reviews and sends feedback directly to implementers via mailbox. |

### Worktree Setup

```bash
BRANCH_NAME=$(git branch --show-current | tr '/' '-')

git worktree add ".worktrees/team-${BRANCH_NAME}-impl-1" HEAD
git worktree add ".worktrees/team-${BRANCH_NAME}-impl-2" HEAD
# Add impl-3 if 5+ tasks

# Ensure .worktrees/ is in .gitignore
```

### Worktree Cleanup

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

---

## Subagent Mode Details

### Dispatch: Implementer (Initial)

```
Task tool:
  subagent_type: implementer
  model: [MODEL from plan, default: sonnet]
  run_in_background: [true if parallelizable, false otherwise]
  description: "Implement Task N: [brief name]"
  prompt: |
    ## Task N: [task name]
    [FULL TEXT of task from plan]

    ## Context
    [Where this fits, dependencies]

    ## Working Directory
    [path]
```

### Dispatch: Implementer (Fix — MINOR)

```
Task tool:
  subagent_type: implementer
  model: haiku  # override for MINOR fixes
  description: "Fix minor issue: [description]"
  prompt: |
    ## Minor Fix Required
    [structured feedback]
```

### Dispatch: Implementer (Fix — STANDARD/COMPLEX)

```
Task tool:
  subagent_type: implementer
  model: [same as original, or escalate to opus for COMPLEX]
  description: "Fix [spec/quality/build] issues for Task N"
  prompt: |
    ## Fix Required
    The [spec/quality/build] review found issues.

    ## Original Task
    [task text for context]

    ## Issues to Fix
    [structured feedback]

    ## Instructions
    1. Fix ONLY the issues mentioned
    2. Don't refactor unrelated code
    3. Run tests to verify
    4. Commit: fix: address [spec/quality] review feedback
```

### Dispatch: Quick Reviewer (SIMPLE tasks)

```
Task tool:
  subagent_type: quick-reviewer
  description: "Quick review for Task N"
  prompt: |
    ## What Was Requested
    [task text]

    ## What Was Built
    [implementer's report]

    ## Files to Inspect
    [list]
```

### Dispatch: Spec Reviewer (STANDARD+ tasks)

```
Task tool:
  subagent_type: spec-reviewer
  description: "Spec review for Task N"
  prompt: |
    ## What Was Requested
    [task text]

    ## What Was Built
    [implementer's report]

    ## Files to Inspect
    [list]
```

### Dispatch: Quality Reviewer (STANDARD+ tasks)

```
Task tool:
  subagent_type: quality-reviewer
  description: "Quality review for Task N"
  prompt: |
    ## Task Context
    [brief description of what was implemented]

    ## Files Changed
    [list]
```

### Dispatch: Staff Code Reviewer (Phase/Final)

```
Task tool:
  subagent_type: staff-code-reviewer
  model: opus
  description: "Phase N review" or "Final review"
  prompt: |
    Comprehensive review.
    Commits: [BASE_SHA]..[HEAD_SHA]
```

### Structured Fix Feedback Format

When dispatching implementer for fixes, use this format:

```json
{
  "iteration": N,
  "status": "review_failure|test_failure|build_failure",
  "file": "path/to/file.ts",
  "issues": [
    {"line": 47, "issue": "description", "fix": "suggested fix"}
  ],
  "previous_fix": "what was tried last",
  "max_attempts": 3
}
```

If JSON validation fails, fall back to plain text:

```
## Fix Required (Attempt N of 3)
Status: [review_failure|test_failure|build_failure]
File: path/to/file.ts
Issues:
1. Line 47: [issue] -> [fix]
Previous attempt: [what was tried]
```

---

## Fix Loop Severity (Both Modes)

| Fix Type | Model | Max Attempts | Indicators |
|----------|-------|--------------|------------|
| MINOR | haiku (override) | 2 | Typo, missing import, lint fix |
| STANDARD | sonnet | 2 | Logic error, error handling, test fix |
| COMPLEX | sonnet -> opus (with approval) | 2 + escalate | Architectural feedback, multi-file fix |

**Escalation for COMPLEX fixes:**
After 2 failed sonnet attempts, ask user for approval:

```
ESCALATION: Complex fix failing after 2 attempts.
Issue: [description]
Options:
1. Escalate to opus (higher cost, better reasoning)
2. Skip and document as known issue
3. Manual intervention
```

## Escalation (Both Modes)

**Escalate to user when:**
- Fix loop exceeds max attempts (3 task-level, 2 phase-level)
- Reviewer and implementer disagree (team mode: after 3 rounds)
- Security concern needs judgment
- Architectural decision needed
- Merge conflicts between worktrees that can't be auto-resolved (team mode)

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

## Red Flags

**Never:**
- Skip verification after fixes
- Let fix loops run indefinitely
- Proceed with CRITICAL issues from phase review
- Use opus for every implementation task
- Leave worktrees behind after completion (team mode)
- Skip the env var check for mode selection

**Always:**
- Classify task complexity before execution
- Use quick-reviewer for SIMPLE tasks (subagent mode)
- Pass specific feedback to fix agents
- Re-verify after every fix
- Track attempts per task
- Escalate when stuck
- Clean up worktrees during final step (team mode)
- Enter delegate mode before spawning teammates (team mode)

## Integration

**Uses:**
- `dev-workflow:staff-code-reviewer` — phase/final reviews (opus)
- `/pr-status` command — CI watch, review comment polling, readiness verdict
- Git worktrees — workspace isolation (team mode)
- Shared task list + mailbox — work coordination (team mode)
- Task tool with `run_in_background` — parallel dispatch (subagent mode)
- `dev-workflow:implementer` — task implementation (subagent mode)
- `dev-workflow:quick-reviewer` — fast combined review for simple tasks (subagent mode)
- `dev-workflow:spec-reviewer` — spec compliance check (subagent mode)
- `dev-workflow:quality-reviewer` — quality gate (subagent mode)

**Works with:**
- `dev-workflow:writing-plans` — creates plans with model recommendations and parallelizable field
- `dev-workflow:brainstorming` — design exploration before planning
- `dev-workflow:systematic-debugging` — bug investigation workflow
- `dev-workflow:test-driven-development` — TDD discipline for implementation
- `dev-workflow:using-git-worktrees` — isolated workspaces
