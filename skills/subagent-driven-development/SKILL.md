---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# Subagent-Driven Development

Execute plan by dispatching implementer agent per task, with verification gates and review loops.

**Core principle:** Implement -> Verify -> Review -> Fix (if needed) -> Loop until pass

## When to Use

- Have an implementation plan with tasks and recommended models
- Tasks are mostly independent
- Want to stay in current session

## Task Classification

Classify each task before dispatching:

| Complexity | Impl Model | Review Path | Indicators |
|------------|------------|-------------|------------|
| SIMPLE | haiku (via Task tool model param) | quick-reviewer only | ≤2 files, config, boilerplate, mechanical |
| STANDARD | sonnet (default) | spec → quality → (phase) | Multi-file, business logic, error handling |
| COMPLEX | sonnet or opus (via Task tool) | spec → quality → phase | Only if plan explicitly requires |

**Note:** The implementer agent defaults to sonnet. To use haiku for simple tasks, pass `model: haiku` in the Task tool call. Planning should recommend models per task.

## Model Selection

**Planning stage** should include model recommendation per task (usually haiku or sonnet).
**Opus** is reserved for:
- Main conversation orchestration
- Staff-code-reviewer (phase/final reviews)
- Only for implementation if plan explicitly says so (rare)

| Role | Agent | Default Model | Override |
|------|-------|---------------|----------|
| Implementer (standard) | implementer | sonnet | haiku if plan says |
| Implementer (simple) | implementer | sonnet | haiku if plan says |
| Quick reviewer | quick-reviewer | haiku | - |
| Spec reviewer | spec-reviewer | sonnet | - |
| Quality reviewer | quality-reviewer | sonnet | - |
| Staff reviewer | staff-code-reviewer | opus | - |

## The Complete Flow

```
SETUP
======================================================================
1. Ensure on feature branch (create if needed)
2. Read plan, extract ALL tasks with:
   - Full task text
   - Recommended model (default: sonnet)
   - Complexity classification (SIMPLE/STANDARD/COMPLEX)
   - Context/dependencies
3. Create TodoWrite with all tasks

PER TASK
======================================================================

+-- IMPLEMENT --------------------------------------------------+
| 4. Mark task in_progress in TodoWrite                         |
| 5. Dispatch implementer agent (model from plan)               |
| 6. If implementer asks questions -> answer -> resume          |
| 7. Implementer: implement -> test -> self-review -> commit    |
+---------------------------------------------------------------+
                              |
                              v
+-- VERIFY -----------------------------------------------------+
| 8. Run verification (typecheck, build, tests)                 |
|                                                               |
|    If FAILS -> dispatch implementer with error output         |
|    -> "Fix these build/type errors"                           |
|    -> Loop back to VERIFY (max 3 attempts, then escalate)     |
+---------------------------------------------------------------+
                              |
                              v
+-- REVIEW (conditional based on complexity) -------------------+
| SIMPLE tasks:                                                 |
|   9a. Dispatch quick-reviewer (haiku) - single pass           |
|                                                               |
| STANDARD+ tasks:                                              |
|   9b. Dispatch spec-reviewer (sonnet)                         |
|   10. Dispatch quality-reviewer (sonnet)                      |
|                                                               |
|   If ISSUES -> dispatch implementer with feedback             |
|   -> Loop to VERIFY then REVIEW (max 3 attempts)              |
+---------------------------------------------------------------+
                              |
                              v
| 11. Mark task completed in TodoWrite                          |
| 12. Continue to next task...                                  |

PHASE BOUNDARY
======================================================================
+-- PHASE REVIEW -----------------------------------------------+
| 13. Skip phase review if ALL tasks in phase were SIMPLE       |
|                                                               |
| Otherwise: Dispatch staff-code-reviewer (opus)                |
|     Commits: [phase_start_sha]..[current_sha]                 |
|                                                               |
|     If CRITICAL/IMPORTANT -> implementer fixes -> re-verify   |
|     -> Re-run staff-code-reviewer (max 2 attempts)            |
+---------------------------------------------------------------+

FINAL
======================================================================
14. Final staff-code-reviewer (opus) - entire implementation
15. Create PR (follow repo template if exists)
16. Invoke /pr-merge workflow (or user invokes manually)
```

## Fix Loop Severity

Classify fix complexity to optimize model usage:

| Fix Type | Model | Max Attempts | Indicators |
|----------|-------|--------------|------------|
| MINOR | haiku (override) | 2 | Typo, missing import, lint fix |
| STANDARD | sonnet | 2 | Logic error, error handling, test fix |
| COMPLEX | sonnet → opus (with approval) | 2 + escalate | Architectural feedback, multi-file fix |

**Escalation for COMPLEX fixes:**
After 2 failed sonnet attempts on a COMPLEX fix, ask user for approval:

```
ESCALATION: Complex fix failing after 2 attempts.
Issue: [description]
Options:
1. Escalate to opus (higher cost, better reasoning)
2. Skip and document as known issue
3. Manual intervention
```

## Structured Fix Feedback Format

When dispatching implementer for fixes, use this JSON format:

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

**Validation:** Before passing feedback JSON to implementer, verify it's valid:
```bash
echo "$FEEDBACK_JSON" | python3 -c "import json,sys; json.load(sys.stdin)" && echo "Valid JSON"
```

If validation fails, fall back to plain text feedback with clear structure:
```
## Fix Required (Attempt N of 3)
Status: [review_failure|test_failure|build_failure]
File: path/to/file.ts
Issues:
1. Line 47: [issue] → [fix]
Previous attempt: [what was tried]
```

## Dispatching Subagents

### Implementer (Initial)
```
Task tool:
  subagent_type: implementer
  model: [MODEL from plan, default: sonnet]
  description: "Implement Task N: [brief name]"
  prompt: |
    ## Task N: [task name]
    [FULL TEXT of task from plan]

    ## Context
    [Where this fits, dependencies]

    ## Working Directory
    [path]
```

### Implementer (Fix Mode - MINOR)
```
Task tool:
  subagent_type: implementer
  model: haiku  # override for MINOR fixes
  description: "Fix minor issue: [description]"
  prompt: |
    ## Minor Fix Required
    [structured feedback JSON]
```

### Implementer (Fix Mode - STANDARD/COMPLEX)
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
    [structured feedback JSON]

    ## Instructions
    1. Fix ONLY the issues mentioned
    2. Don't refactor unrelated code
    3. Run tests to verify
    4. Commit: fix: address [spec/quality] review feedback
```

### Quick Reviewer (SIMPLE tasks only)
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

### Spec Reviewer (STANDARD+ tasks)
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

### Quality Reviewer (STANDARD+ tasks)
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

### Staff Code Reviewer (Phase/Final)
```
Task tool:
  subagent_type: staff-code-reviewer
  model: opus
  description: "Phase N review" or "Final review"
  prompt: |
    Comprehensive review.
    Commits: [BASE_SHA]..[HEAD_SHA]
```

## Escalation

**Escalate to user when:**
- Fix loop exceeds max attempts (3 task-level, 2 phase-level)
- Reviewer and implementer disagree
- Security concern needs judgment
- Architectural decision needed

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
- Skip verification step
- Skip re-verification after fixes
- Let fix loops run indefinitely
- Proceed with CRITICAL issues
- Use opus for every implementation task

**Always:**
- Classify task complexity before dispatching
- Use quick-reviewer for SIMPLE tasks
- Pass specific feedback to fix subagents (use JSON format)
- Re-verify after every fix
- Re-review after fixes
- Track attempts
- Escalate when stuck

## Integration

**Uses:**
- `dev-workflow:implementer` - task implementation (sonnet, or haiku if plan specifies)
- `dev-workflow:quick-reviewer` - fast combined review for simple tasks (haiku)
- `dev-workflow:spec-reviewer` - spec compliance check (sonnet)
- `dev-workflow:quality-reviewer` - quick quality gate (sonnet)
- `dev-workflow:staff-code-reviewer` - comprehensive phase/final reviews (opus)
- `/pr-merge` command - CI check, comment assessment, merge

**Works with:**
- `superpowers:writing-plans` - creates plans with model recommendations
