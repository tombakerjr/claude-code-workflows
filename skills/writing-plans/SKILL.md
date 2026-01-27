---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Implementation Plans

Create structured plans that chain to subagent-driven-development for execution.

**Core principle:** Plan with bite-sized tasks, model recommendations, and TDD embedded.

## When to Use

- Have spec or requirements
- Task requires multiple steps (3+)
- Need to coordinate work across multiple files/components
- Want to ensure thorough testing and review

**Don't use for:**
- Single-file, single-step changes (just implement)
- Trivial updates (config changes, version bumps)
- Exploratory work (use brainstorming first)

## Plan Structure

```markdown
# Implementation Plan: [Feature/Component Name]

**Skill:** `dev-workflow:subagent-driven-development`

## Overview
[1-2 sentences on what we're building and why]

## Prerequisites
- [Required context, dependencies, or setup]

## Phase 1: [Phase Name]
[Brief description of what this phase accomplishes]

### Task 1.1: [Brief imperative title]
**Model:** haiku | sonnet | opus
**Complexity:** SIMPLE | STANDARD | COMPLEX

[Description of what to implement]

**Acceptance criteria:**
- [ ] [Specific, testable criterion]
- [ ] [Another criterion]

**Testing approach:** [TDD steps or test types needed]

### Task 1.2: [Next task]
...

## Phase 2: [Next Phase Name]
...

## Verification
- [ ] All tests pass
- [ ] Typecheck passes
- [ ] Build succeeds
- [ ] Manual testing: [specific scenarios]

## Review Checkpoints
- After Phase 1: spec + quality review
- After Phase 2: spec + quality review
- Final: staff-code-reviewer (opus)
```

## Model Selection Guide

Choose model based on task complexity:

| Complexity | Model | When to Use | Indicators |
|------------|-------|-------------|------------|
| **SIMPLE** | haiku | Mechanical, low-risk | ≤2 files, config, types, boilerplate, doc updates |
| **STANDARD** | sonnet | Typical feature work | Multi-file, business logic, error handling, API changes |
| **COMPLEX** | sonnet/opus | High-risk or novel | Architecture changes, security, performance-critical, unfamiliar patterns |

**Default to sonnet** unless the task clearly fits SIMPLE or explicitly requires COMPLEX reasoning.

**Reserve opus for:**
- Staff-level reviews (phase boundaries, final review)
- Complex architectural decisions in implementation (rare)
- Main conversation orchestration

## Task Structure

### Anatomy of a Good Task

```markdown
### Task 1.1: Add user authentication endpoint
**Model:** sonnet
**Complexity:** STANDARD

Create POST /auth/login endpoint that validates credentials and returns JWT token.

**Implementation details:**
- Accept email + password in request body
- Validate against database
- Return JWT with 1h expiration
- Return 401 for invalid credentials

**Acceptance criteria:**
- [ ] Endpoint responds at POST /auth/login
- [ ] Valid credentials return 200 with JWT
- [ ] Invalid credentials return 401
- [ ] Token includes user ID and expires in 1h

**Testing approach:**
- RED: Write test for valid credentials → expect JWT
- GREEN: Implement validation and token generation
- RED: Write test for invalid credentials → expect 401
- GREEN: Add error handling
- REFACTOR: Extract token generation to service
```

### What Makes a Task "Bite-Sized"

✅ **Good task size:**
- Implementable in one focused session (30-60 min)
- Single responsibility or feature slice
- Clear acceptance criteria
- Self-contained (minimal dependencies on incomplete work)

❌ **Too large:**
- "Implement entire authentication system"
- "Add user management"
- Multiple independent features bundled

❌ **Too small:**
- "Add import statement"
- "Fix typo in comment"
- Trivial changes that aren't worth separate tasks

### Task Dependencies

**Prefer independent tasks** that can be worked on in any order.

If dependencies exist:
```markdown
### Task 1.2: Add token refresh endpoint
**Model:** sonnet
**Complexity:** STANDARD
**Depends on:** Task 1.1 (uses same token generation)

[Task description...]
```

## TDD Embedded in Tasks

**Every task that writes code should specify testing approach.**

### For Features (TDD Cycle)
```markdown
**Testing approach:**
- RED: Write test for [expected behavior]
- GREEN: Implement [minimal code to pass]
- RED: Write test for [edge case]
- GREEN: Handle [edge case]
- REFACTOR: [Extract/improve code]
```

### For Bugs (Systematic Debugging → TDD)
```markdown
**Testing approach:**
- Reproduce bug in failing test (exposes root cause)
- RED: Confirm test fails with bug present
- GREEN: Implement fix
- Verify original issue resolved
```

### For Refactoring (Test-First Safety)
```markdown
**Testing approach:**
- Ensure existing tests cover current behavior
- Add tests for edge cases if missing
- Refactor while keeping all tests green
```

## Phase Boundaries

**Break work into phases when:**
- Natural checkpoint exists (e.g., "core implementation" then "integration")
- Want to review intermediate state before continuing
- Tasks in later phases depend on earlier ones

**Review at phase boundaries:**
- SIMPLE-only phases: Skip phase review
- STANDARD+ phases: staff-code-reviewer (opus)

## Anti-Patterns to Avoid

❌ **Tasks too large**
- "Implement entire feature" → Break into smaller pieces
- Multiple independent changes → Separate tasks

❌ **No model recommendations**
- Every task should specify haiku/sonnet/opus
- Defaults to sonnet if unspecified, but be explicit

❌ **Missing testing approach**
- Tasks that write code must specify how to test
- TDD should be the default, not optional

❌ **Vague acceptance criteria**
- "Works correctly" → Specify exactly what "works" means
- "Handles errors" → Which errors? What responses?

❌ **No complexity classification**
- Needed for review path selection
- Helps estimate effort and choose model

❌ **Sequential dependencies everywhere**
- Makes parallel work impossible
- Prefer independent tasks when possible

## Example Plans

### Example 1: Simple Feature (3 Tasks)

```markdown
# Implementation Plan: Add Health Check Endpoint

**Skill:** `dev-workflow:subagent-driven-development`

## Overview
Add GET /health endpoint that returns service status and dependencies.

## Prerequisites
- Express server already set up
- Database connection exists

## Phase 1: Implementation

### Task 1.1: Create health check endpoint
**Model:** haiku
**Complexity:** SIMPLE

Add GET /health that returns 200 OK with JSON status.

**Acceptance criteria:**
- [ ] GET /health returns 200
- [ ] Response includes { status: "ok", timestamp: ISO string }

**Testing approach:**
- RED: Request GET /health → expect 200 with status
- GREEN: Create endpoint handler
- REFACTOR: Extract status builder if needed

### Task 1.2: Add database health check
**Model:** sonnet
**Complexity:** STANDARD

Extend health endpoint to check database connectivity.

**Acceptance criteria:**
- [ ] Health check attempts database ping
- [ ] Returns db: "healthy" if connection succeeds
- [ ] Returns db: "unhealthy" if connection fails
- [ ] Overall status is "ok" only if all checks pass

**Testing approach:**
- RED: Test with healthy db → expect db: "healthy"
- GREEN: Implement db ping check
- RED: Test with failed db → expect db: "unhealthy"
- GREEN: Add error handling
- REFACTOR: Extract check logic to service

### Task 1.3: Add documentation
**Model:** haiku
**Complexity:** SIMPLE

Document the health check endpoint in API docs.

**Acceptance criteria:**
- [ ] API.md includes GET /health
- [ ] Response format documented
- [ ] Status values explained

**Testing approach:** N/A (documentation only)

## Verification
- [ ] All tests pass
- [ ] GET /health returns correct format
- [ ] Manual test: kill database, verify unhealthy status

## Review Checkpoints
- After Phase 1: spec + quality review
- Final: staff-code-reviewer (opus)
```

### Example 2: Multi-Phase Feature

```markdown
# Implementation Plan: User Profile Management

**Skill:** `dev-workflow:subagent-driven-development`

## Overview
Implement CRUD operations for user profiles with validation and permissions.

## Prerequisites
- User authentication system exists (JWT auth)
- Database schema includes users table

## Phase 1: Core Profile Operations

### Task 1.1: Create profile data model
**Model:** haiku
**Complexity:** SIMPLE

Define TypeScript interface and database schema for user profiles.

**Acceptance criteria:**
- [ ] Profile interface includes: name, email, bio, avatarUrl
- [ ] Database migration creates profiles table
- [ ] Foreign key to users table

**Testing approach:**
- Verify migration runs successfully
- Verify schema matches interface

### Task 1.2: Implement GET /profile/:id
**Model:** sonnet
**Complexity:** STANDARD

Create endpoint to fetch user profile by ID.

**Acceptance criteria:**
- [ ] GET /profile/:id returns profile data
- [ ] Returns 404 if profile doesn't exist
- [ ] Excludes sensitive fields (password, etc.)

**Testing approach:**
- RED: Request existing profile → expect 200 with data
- GREEN: Implement fetch logic
- RED: Request missing profile → expect 404
- GREEN: Add not-found handling
- REFACTOR: Extract data mapping to service

### Task 1.3: Implement PUT /profile/:id
**Model:** sonnet
**Complexity:** STANDARD

Create endpoint to update user profile with permission checks.

**Acceptance criteria:**
- [ ] PUT /profile/:id updates profile fields
- [ ] Requires authentication
- [ ] Users can only update their own profile
- [ ] Returns 403 for unauthorized updates
- [ ] Validates input (email format, bio length, etc.)

**Testing approach:**
- RED: Authenticated user updates own profile → expect 200
- GREEN: Implement update logic
- RED: User tries to update different profile → expect 403
- GREEN: Add permission check
- RED: Invalid input → expect 400 with validation errors
- GREEN: Add validation
- REFACTOR: Extract permission logic to middleware

## Phase 2: Profile Features

### Task 2.1: Add profile picture upload
**Model:** sonnet
**Complexity:** STANDARD

Allow users to upload profile pictures with validation.

**Acceptance criteria:**
- [ ] POST /profile/:id/avatar accepts image file
- [ ] Validates file type (jpg, png, max 5MB)
- [ ] Stores in S3/storage service
- [ ] Updates avatarUrl in profile
- [ ] Returns 400 for invalid files

**Testing approach:**
- RED: Upload valid image → expect 200 with URL
- GREEN: Implement upload to storage
- RED: Upload invalid file → expect 400
- GREEN: Add validation
- RED: Upload over size limit → expect 400
- GREEN: Add size check
- REFACTOR: Extract upload logic to service

### Task 2.2: Add profile search
**Model:** sonnet
**Complexity:** STANDARD

Create endpoint to search profiles by name or email.

**Acceptance criteria:**
- [ ] GET /profiles?q=query returns matching profiles
- [ ] Searches name and email fields
- [ ] Case-insensitive search
- [ ] Returns max 20 results
- [ ] Excludes private profiles

**Testing approach:**
- RED: Search by name → expect matching results
- GREEN: Implement basic search
- RED: Search with case variations → expect same results
- GREEN: Make search case-insensitive
- REFACTOR: Extract query builder

## Verification
- [ ] All tests pass (unit + integration)
- [ ] Typecheck passes
- [ ] Manual testing: CRUD operations work end-to-end
- [ ] Permission checks enforced

## Review Checkpoints
- After Phase 1: spec + quality review
- After Phase 2: spec + quality review
- Final: staff-code-reviewer (opus)
```

## Integration

**Creates plans for:**
- `dev-workflow:subagent-driven-development` - executes the plan

**Works with:**
- `superpowers:brainstorming` - use before planning if requirements unclear
- `dev-workflow:test-driven-development` - embedded in task structure
- `dev-workflow:systematic-debugging` - for bug fix plans

## Success Criteria

✅ Plan has clear phases and bite-sized tasks
✅ Every task specifies model (haiku/sonnet/opus)
✅ Every task classified by complexity (SIMPLE/STANDARD/COMPLEX)
✅ Tasks that write code include testing approach
✅ Acceptance criteria are specific and testable
✅ Review checkpoints identified
✅ Plan chains to subagent-driven-development for execution

## Chains To

After writing plan, invoke:
```
/skill dev-workflow:subagent-driven-development
```

The execution skill will:
1. Read this plan
2. Extract all tasks with model recommendations
3. Dispatch implementer per task (using recommended model)
4. Run verification and reviews at specified checkpoints
5. Complete implementation following the plan structure
