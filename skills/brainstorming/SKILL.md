---
name: brainstorming
description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
---

# Brainstorming

## Iron Law

**No implementation without design dialogue first.**

When faced with creative work (new features, components, behavior changes), you must understand the problem deeply before jumping to solutions. Design emerges through conversation, not upfront specification.

## The Socratic Approach

### Ask ONE Question at a Time

**Never present a list of questions.** Each question is an opportunity to learn and adjust the next question based on the answer.

Good:
```
What's the primary goal of this feature?

A) Enable users to export data
B) Provide admin oversight
C) Integrate with external system
D) Other (please describe)
```

Bad:
```
I need to understand:
1. What's the primary goal?
2. Who are the users?
3. What are the constraints?
4. How does this integrate?
5. What's the timeline?
```

### Prefer Multiple Choice

**Reduce user typing burden.** Offer options based on common patterns, always include "Other" as escape hatch.

Structure:
- 3-5 clear options
- One "Other (please describe)" option
- Brief explanation if options need context

### Build Understanding Incrementally

**Each answer shapes the next question.** Don't follow a rigid script. Adapt based on what you learn.

Flow:
1. Start broad (what/why)
2. Narrow to specifics (who/when/where)
3. Explore constraints (technical/timeline/resources)
4. Consider alternatives (tradeoffs)

## The Design Document

### Structure (200-300 Word Sections)

Build the design in digestible chunks. After each section, pause for validation.

**Section 1: Problem Statement**
- What problem exists?
- Who experiences it?
- Why does it matter?
- Current workarounds (if any)

**Validation:** "Does this accurately capture the problem you're trying to solve?"

**Section 2: Proposed Solution**
- High-level approach
- Key architectural decisions
- How it addresses the problem
- What's explicitly out of scope

**Validation:** "Does this direction align with your vision?"

**Section 3: Technical Design**
- Components/modules involved
- Data models or structures
- Integration points
- Error handling approach

**Validation:** "Any technical concerns or missing pieces?"

**Section 4: Implementation Notes**
- Development phases (if multi-part)
- Testing strategy
- Migration/rollout plan
- Success metrics

**Validation:** "Anything we should prioritize or defer?"

### Save Location

```
docs/plans/YYYY-MM-DD-<topic>-design.md
```

Topic should be kebab-case, descriptive. Examples:
- `2026-01-27-user-export-feature-design.md`
- `2026-01-27-admin-dashboard-redesign.md`
- `2026-01-27-payment-integration-design.md`

## Process

### 1. Understand the Problem

**Questions to explore:**
- What needs to exist or change? (multiple choice of common patterns)
- Why is this important now? (priority/urgency)
- Who will use or benefit from this? (users/stakeholders)
- What constraints exist? (technical/timeline/resources)

**Checkpoint:** You understand the "why" behind the work.

### 2. Explore Solutions

**Questions to explore:**
- What approaches have you considered? (list options, ask to pick or add)
- What tradeoffs matter most? (speed vs. flexibility, simple vs. complete)
- Are there existing patterns in the codebase to follow? (consistency)
- What could go wrong? (risks/edge cases)

**Checkpoint:** Multiple options identified, tradeoffs clear.

### 3. Design the Solution

**Build the document section by section:**
1. Write Problem Statement → validate
2. Write Proposed Solution → validate
3. Write Technical Design → validate
4. Write Implementation Notes → validate

**Checkpoint:** Complete design document saved to docs/plans/.

### 4. Prepare for Implementation

**Chain to related skills:**

```
Should we set up an isolated workspace for this work?

A) Yes - use git worktrees for clean separation
B) No - work directly in current branch
```

If A: Chain to `dev-workflow:using-git-worktrees`

Then:

```
Ready to create implementation plan?

This will break the design into concrete tasks with verification steps.
```

Chain to `superpowers:writing-plans`

## When to Use This Skill

**Always use for:**
- New features or capabilities
- Significant behavior changes
- UI/UX components or flows
- Architecture decisions
- Integration with external systems
- Refactoring with unclear scope

**Use when requirements are:**
- Vague or high-level ("make it better")
- Creative ("design a dashboard")
- Complex (multiple components/stakeholders)
- Risky (big changes, unclear impact)

**Skip when:**
- Fixing clear bugs (use systematic-debugging)
- Implementing from detailed spec
- Making trivial changes (typos, formatting)

## Integration with Other Skills

**Chains to `dev-workflow:using-git-worktrees`:**
- After design is complete, offer to set up isolated workspace
- Worktree provides clean environment for implementation
- Easy to abandon if design changes during implementation

**Chains to `superpowers:writing-plans`:**
- Design document becomes input to planning
- Plan breaks design into tasks with verification
- Each task references relevant sections of design

**Works with `dev-workflow:implementer`:**
- Implementer references design document during work
- Design provides context for decisions
- Implementation may surface design issues (feedback loop)

## Anti-Patterns to Avoid

❌ Asking multiple questions at once (overwhelming)
❌ Open-ended questions when multiple choice would work (too much typing)
❌ Writing full design without validation (wasted effort)
❌ Skipping problem exploration and jumping to solution
❌ Not documenting the design (context loss)
❌ Continuing to implementation without user sign-off

## Success Criteria

✅ Problem is clearly understood and documented
✅ Multiple solution approaches were considered
✅ Design choices have clear rationale (tradeoffs)
✅ User validated each section before continuing
✅ Complete design saved to docs/plans/
✅ Clear path to implementation (chained to worktrees/planning)

## Example Flow

```
USER: "I want to add user exports to the admin panel"

ASSISTANT: Let me understand what you're trying to accomplish.

What's the primary goal of this export feature?

A) Enable admins to audit user activity
B) Provide data portability for users
C) Generate reports for compliance
D) Other (please describe)

USER: "A - audit user activity"

ASSISTANT: Got it, auditing focus.

What format would be most useful for admins?

A) CSV (spreadsheet-compatible)
B) JSON (programmatic processing)
C) PDF (human-readable report)
D) Multiple formats (let admin choose)

USER: "A - CSV is fine"

ASSISTANT: Perfect, CSV keeps it simple.

Should this export:

A) All users (full database dump)
B) Filtered subset (search/filter first)
C) Single user (from user detail page)
D) Multiple options above

USER: "B - filtered subset"

ASSISTANT: Makes sense, working with existing filters.

[Continue dialogue, then...]

I'll now write up the Problem Statement section:

---
**Problem Statement**

Admins need to export filtered user lists as CSV for audit purposes.
Currently, they must manually copy data from the UI table, which is
error-prone and limited by pagination. This blocks quarterly compliance
reviews where admins must analyze user activity patterns across hundreds
of users.

**Who experiences it:** Admin users performing audits/compliance reviews

**Why it matters:** Manual data collection is time-consuming and creates
compliance risk if data is incomplete or incorrect.

**Current workaround:** Copy-paste from UI table, limited to current page
---

Does this accurately capture the problem you're trying to solve?

USER: "Yes, that's right"

ASSISTANT: Great. Now for the Proposed Solution...

[Continue through all sections, validate each, then save]

Design complete! I've saved it to:
docs/plans/2026-01-27-admin-user-export-design.md

Should we set up an isolated workspace for this work?

A) Yes - use git worktrees for clean separation
B) No - work directly in current branch
```
