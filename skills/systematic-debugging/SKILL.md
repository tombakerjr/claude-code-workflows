---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Iron Law

**No fixes without root cause identification first.**

You may not propose or implement fixes until you understand why the system is behaving incorrectly. If you don't know the root cause, you must investigate further.

## The 4-Phase Framework

### 1. Investigate - Gather Evidence

**Reproduce and observe:**
1. Reproduce the bug reliably in isolation
2. Document exact steps to trigger the behavior
3. Capture error messages, stack traces, logs
4. Identify what works vs. what fails (boundary conditions)
5. Check when this last worked (git bisect if needed)

**Checkpoint:** Bug is reproducible. Evidence is documented.

### 2. Analyze - Understand the System

**Study the code paths:**
1. Read the code where the bug manifests
2. Trace the execution flow backward from symptom
3. Identify assumptions in the code
4. Check related test coverage (what's tested vs. not)
5. Look for recent changes in this area

**Checkpoint:** You understand what the code is trying to do and where it deviates.

### 3. Hypothesize - Form Root Cause Theory

**Develop testable hypothesis:**
1. State your theory about WHY the bug occurs
2. Predict what would happen if theory is correct
3. Identify evidence that would confirm or refute theory
4. Test hypothesis (add logging, debugger, or minimal test case)
5. Refine theory based on results

**Checkpoint:** You have a theory that explains all observed symptoms.

### 4. Implement - Fix Using TDD

**Use test-driven development:**
1. Chain to `dev-workflow:test-driven-development` skill
2. Write failing test that exposes the bug (RED)
3. Implement minimal fix (GREEN)
4. Refactor if needed (REFACTOR)
5. Verify original reproduction steps now pass

**Checkpoint:** Bug is fixed. Test prevents regression.

## The 3-Fix Rule

**After 3 failed fix attempts, STOP and reassess:**

1. **Question your assumptions** - What if your mental model is wrong?
2. **Broaden the search** - Is the real cause elsewhere in the system?
3. **Escalate or pair** - Get fresh eyes on the problem
4. **Consider architectural issues** - Maybe the design makes this bug inevitable

Don't keep trying variations. If 3 attempts failed, your understanding is incomplete.

## Process

### Starting a Debug Session

1. **Document the symptom** - What's wrong? Expected vs. actual behavior
2. **Reproduce reliably** - Can you trigger it on demand?
3. **Gather evidence** - Error messages, logs, stack traces
4. **Analyze the system** - Read code, understand flow
5. **Form hypothesis** - Why does this happen?
6. **Test hypothesis** - Prove or disprove your theory
7. **Fix with TDD** - Write test, implement fix, verify

### Verification at Each Phase

- After INVESTIGATE: Bug reproduces consistently
- After ANALYZE: You understand the code's intent and actual behavior
- After HYPOTHESIZE: Theory explains all symptoms
- After IMPLEMENT: Bug is fixed, tests pass, no regression

## When to Use This Skill

**Always use for:**
- Test failures (existing tests that started failing)
- Production bugs (unexpected behavior in live code)
- Integration issues (two components don't work together)
- Performance regressions (something got slower)
- Intermittent failures (flaky tests, race conditions)

**This is the required approach for all debugging work.**

## Integration with Other Skills

**Chains to `dev-workflow:test-driven-development`:**
- Phase 1-3 (Investigate/Analyze/Hypothesize) identify root cause
- Phase 4 uses TDD to implement fix
- TDD's RED step writes test that exposes bug
- TDD's GREEN step implements minimal fix
- Result: Bug fixed + regression test added

**Works with `dev-workflow:implementer`:**
- Implementer invokes systematic-debugging when tests fail
- Follows 4-phase framework to understand failure
- Uses TDD to implement fix

**Works with `dev-workflow:plan-execution`:**
- When verification step fails, orchestrator may invoke debugger
- Debugger identifies root cause, TDD implements fix
- Re-verify in main workflow loop

## Anti-Patterns to Avoid

❌ Trying random fixes hoping something works
❌ Fixing symptoms without understanding cause
❌ Skipping hypothesis phase and jumping to implementation
❌ Not reproducing the bug before claiming it's fixed
❌ Continuing past 3 failed attempts without reassessing
❌ Implementing fixes without tests

## Success Criteria

✅ Root cause is clearly identified and explained
✅ Hypothesis was tested and confirmed before fixing
✅ Fix has corresponding test that would catch regression
✅ Original reproduction steps now pass
✅ No new failures introduced
✅ If 3 attempts failed, escalation or reassessment occurred

## Example Flow

```
BUG: User login fails with "Invalid token" error

Phase 1 - INVESTIGATE
- Reproduced: POST /login with valid credentials → 401
- Stack trace shows: TokenValidator.verify() throwing
- Works in dev, fails in staging
- Started failing after deploy 2 days ago

Phase 2 - ANALYZE
- Read TokenValidator code: checks exp claim
- Token generation: sets exp to 1h from now
- Environment difference: staging uses UTC, dev uses local time
- Recent change: Updated time library 2 days ago

Phase 3 - HYPOTHESIZE
Theory: New time library returns different timezone format,
causing exp claim to be misinterpreted in staging.

Test: Add logging to show exact exp value and current time.
Result: Confirmed - exp is ISO string, validator expects Unix timestamp.

Phase 4 - IMPLEMENT
→ Invoke dev-workflow:test-driven-development
→ RED: Write test with ISO exp format → expect to pass
→ GREEN: Update TokenValidator to handle both formats
→ REFACTOR: Clean up time handling
→ VERIFY: All tests pass, staging login works
```
