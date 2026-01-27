---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development

## Iron Law

**No production code without a failing test first.**

You may only write production code to make a failing test pass. If there is no failing test, you must write one before implementing.

## The Red-Green-Refactor Cycle

### 1. Red - Write a Failing Test

**Before any implementation:**
1. Write the smallest test that specifies the next piece of behavior
2. Run the test and verify it fails for the right reason
3. Confirm the failure message indicates what's missing

**Checkpoint:** Test exists and fails with expected error message.

### 2. Green - Make it Pass

**Write minimal implementation:**
1. Write only enough code to make the test pass
2. No additional features or "might need later" code
3. Run the test and verify it passes

**Checkpoint:** Test passes. All existing tests still pass.

### 3. Refactor - Clean up

**Improve without changing behavior:**
1. Remove duplication between test and implementation
2. Improve names, structure, and readability
3. Run all tests to verify behavior unchanged

**Checkpoint:** All tests pass. Code is cleaner than before.

## Process

### Starting a Feature or Bugfix

1. **Understand the requirement** - What behavior needs to exist or change?
2. **Write the test first** - Describe the expected behavior in test form
3. **Watch it fail** - Confirm current code doesn't already do this
4. **Implement minimally** - Make the test pass, nothing more
5. **Refactor** - Clean up while keeping tests green
6. **Repeat** - Next piece of behavior

### Verification at Each Step

- After RED: Test fails with clear, expected error
- After GREEN: This test passes, all tests pass
- After REFACTOR: All tests still pass, code improved

## When to Use This Skill

**Always use for:**
- New features (any size)
- Bug fixes (write test that exposes bug, then fix)
- Refactoring (tests prove behavior unchanged)
- API changes (test new contract first)

**This is the default mode for implementation work.**

## Integration with Other Skills

**Works with `dev-workflow:systematic-debugging`:**
- Debugging finds root cause → TDD writes test that exposes it → TDD fixes it
- The test from TDD becomes the regression test

**Works with `dev-workflow:implementer`:**
- Implementer follows TDD cycle for each task in the plan
- Each commit includes both test and implementation

## Anti-Patterns to Avoid

❌ Writing tests after implementation ("test-after")
❌ Writing implementation for "future needs" without tests
❌ Skipping the RED phase (assuming test would fail)
❌ Writing multiple tests before any implementation
❌ Committing code without tests

## Success Criteria

✅ Every production code change has a corresponding test
✅ Tests were written before the implementation
✅ Each test failed before its implementation was written
✅ All tests pass before moving to next requirement
✅ Code is clean and well-factored
