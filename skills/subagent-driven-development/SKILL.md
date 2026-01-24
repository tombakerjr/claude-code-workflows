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
+-- SPEC REVIEW ------------------------------------------------+
| 9. Dispatch spec reviewer (sonnet)                            |
|                                                               |
|    If ISSUES -> dispatch implementer with feedback            |
|    -> Loop to VERIFY then SPEC REVIEW (max 3 attempts)        |
+---------------------------------------------------------------+
                              |
                              v
+-- QUALITY REVIEW ---------------------------------------------+
| 10. Dispatch code quality reviewer (sonnet)                   |
|                                                               |
|     If CRITICAL/IMPORTANT -> dispatch implementer with        |
|     feedback -> Loop to VERIFY then QUALITY REVIEW            |
|     (max 3 attempts)                                          |
|     MINOR issues: Note, don't block                           |
+---------------------------------------------------------------+
                              |
                              v
| 11. Mark task completed in TodoWrite                          |
| 12. Continue to next task...                                  |

PHASE BOUNDARY
======================================================================
+-- PHASE REVIEW -----------------------------------------------+
| 13. Dispatch staff-code-reviewer (opus)                       |
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

### Implementer (Fix Mode)
```
Task tool:
  subagent_type: implementer
  model: [same as original]
  description: "Fix [spec/quality/build] issues for Task N"
  prompt: |
    ## Fix Required
    The [spec/quality/build] review found issues.

    ## Original Task
    [task text for context]

    ## Issues to Fix
    [EXACT FEEDBACK from reviewer]

    ## Instructions
    1. Fix ONLY the issues mentioned
    2. Don't refactor unrelated code
    3. Run tests to verify
    4. Commit: fix: address [spec/quality] review feedback
```

### Spec Reviewer
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

### Quality Reviewer
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
- Pass specific feedback to fix subagents
- Re-verify after every fix
- Re-review after fixes
- Track attempts
- Escalate when stuck

## Integration

**Uses:**
- `dev-workflow:implementer` - task implementation (sonnet, or haiku if plan specifies)
- `dev-workflow:spec-reviewer` - spec compliance check (sonnet)
- `dev-workflow:quality-reviewer` - quick quality gate (sonnet)
- `dev-workflow:staff-code-reviewer` - comprehensive phase/final reviews (opus)
- `/pr-merge` command - CI check, comment assessment, merge

**Works with:**
- `superpowers:writing-plans` - creates plans with model recommendations
