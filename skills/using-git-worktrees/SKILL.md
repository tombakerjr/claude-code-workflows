---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Iron Law

**One worktree per feature branch to avoid git index conflicts.**

When running multiple implementer agents in parallel or executing implementation plans with isolated workspaces, worktrees prevent git index conflicts and provide clean workspace isolation.

## When to Use This Skill

**Always use for:**
- Executing implementation plans with `dev-workflow:subagent-driven-development`
- Running multiple implementer agents in parallel
- Starting feature work that needs isolation from main workspace
- Working on multiple features simultaneously without switching branches

**This prevents:**
- Git index conflicts between parallel agents
- Accidental changes to main branch workspace
- Stale file state when switching branches
- Build artifacts polluting git status

## Why Worktrees

Git worktrees allow multiple working directories for the same repository:

- **Parallel Development**: Multiple agents can work simultaneously without conflicts
- **Clean Workspace**: Each feature gets its own directory with fresh state
- **Fast Switching**: No need to stash/commit when checking other branches
- **Isolated Builds**: Dependencies and artifacts stay separate per worktree

## The Setup Process

### Phase 1: Safety Checks

**Verify current state is clean:**

```bash
# Check if we're in a clean state
git status

# Check if branch name already exists (local or remote)
git branch -a | grep feature-name
```

**Checkpoint:** Main repo is clean. Branch name is available.

### Phase 2: Create Branch and Worktree

**Create the feature branch:**

```bash
# Create branch from current HEAD (usually main)
git branch feature-name
```

**Create worktree inside the repo's `.worktrees/` directory:**

```bash
# Internal directory pattern: .worktrees/BRANCH_NAME
# Example: .worktrees/feature-auth

git worktree add .worktrees/feature-auth feature-auth
```

**Directory naming convention:**
- Pattern: `.worktrees/BRANCH_NAME`
- Example: `.worktrees/feature-auth`
- Stays inside the repo, respecting Claude Code's permission scoping
- No additional user approval needed for file operations
- Ensure `.worktrees/` is in `.gitignore`

**Checkpoint:** Worktree created. Directory exists.

### Phase 3: Verify Worktree

**Verify worktree state (use `git -C` from the main repo):**

```bash
# Confirm branch and clean state in the worktree
git -C .worktrees/feature-auth status

# Verify worktree list
git worktree list
```

**Checkpoint:** Worktree exists. Branch is correct. State is clean.

### Phase 4: Chain to Implementation Planning

**Now that worktree is set up, chain to writing-plans:**

```
The worktree is ready. I'll now invoke the writing-plans skill
to create the implementation plan for [feature description].
```

The implementation plan will execute in this isolated worktree, preventing any conflicts with the main workspace.

## The Cleanup Process

### After Feature is Complete

**When work is merged or PR is created:**

1. **Remove worktree:**

```bash
# Remove worktree directory and unregister it
git worktree remove .worktrees/feature-auth

# Or if directory was manually deleted:
git worktree prune
```

2. **Delete branch (if merged):**

```bash
# Delete local branch
git branch -d feature-auth

# Delete remote branch if pushed
git push origin --delete feature-auth
```

**Checkpoint:** Worktree removed. Branch deleted if merged.

### Cleanup Verification

```bash
# List remaining worktrees
git worktree list

# Should only show main worktree
```

## Common Commands Reference

### Creating Worktrees

```bash
# Create worktree for new branch
git worktree add .worktrees/branch-name branch-name

# Create worktree for existing branch
git worktree add .worktrees/existing-branch existing-branch

# Create worktree and new branch from specific commit
git worktree add -b new-branch .worktrees/new-branch abc123
```

### Managing Worktrees

```bash
# List all worktrees
git worktree list

# Remove specific worktree
git worktree remove .worktrees/branch-name

# Remove worktree (if already deleted manually)
git worktree prune

# Remove worktree with uncommitted changes (force)
git worktree remove --force .worktrees/branch-name
```

### Working in Worktrees

```bash
# Use git -C to run commands in worktree from the main repo
git -C .worktrees/branch-name status
git -C .worktrees/branch-name add .
git -C .worktrees/branch-name commit -m "feat: implement feature"
git -C .worktrees/branch-name push origin branch-name
```

## Process Flow

### Starting Feature Work with Worktree

1. **Verify main repo state** - `git status` shows clean
2. **Check branch availability** - `git branch -a | grep feature-name` is empty
3. **Create feature branch** - `git branch feature-name`
4. **Create worktree** - `git worktree add .worktrees/feature-name feature-name`
5. **Verify worktree** - `git -C .worktrees/feature-name status`, `git worktree list`
6. **Chain to writing-plans** - Ready for implementation planning

### Verification at Each Phase

- After SAFETY CHECKS: Main clean, branch name available
- After CREATE: Worktree exists, branch created
- After VERIFY: Worktree on correct branch, state is clean
- After CHAIN: Implementation plan can execute in isolation

## Integration with Other Skills

**Chains to `dev-workflow:writing-plans`:**
- Set up worktree first for isolated workspace
- Then invoke writing-plans in the worktree context
- Implementation plan executes in clean, isolated environment

**Works with `dev-workflow:subagent-driven-development`:**
- Worktree provides isolated workspace for plan execution
- Prevents git index conflicts between parallel implementers
- Each task in plan works in same worktree context

**Works with `dev-workflow:implementer`:**
- Implementer agents work in dedicated worktree
- No conflicts with main workspace or other agents
- Clean state for each feature branch

## Anti-Patterns to Avoid

❌ Creating worktree when main repo is dirty
❌ Using branch name that already exists
❌ Creating worktrees as sibling directories outside the repo (breaks permission scoping)
❌ Forgetting to verify worktree state after creation
❌ Leaving worktrees around after feature is merged
❌ Using worktree for quick branch switches (just use `git switch`)
❌ Creating nested worktrees
❌ Forgetting to add `.worktrees/` to `.gitignore`

## Success Criteria

✅ Main repo state is clean before worktree creation
✅ Branch name is unique (doesn't exist locally or remotely)
✅ Worktree created inside `.worktrees/` directory
✅ `.worktrees/` is in `.gitignore`
✅ Worktree list shows both main and new worktree
✅ Implementation plan chains after worktree setup
✅ Cleanup performed after feature merge/completion

## Example Flow

```
SCENARIO: Implementing new authentication feature with parallel agents

Phase 1 - SAFETY CHECKS
$ git status
  → On branch main, working tree clean ✓
$ git branch -a | grep feature-auth
  → No output, branch name available ✓

Phase 2 - CREATE
$ git branch feature-auth
$ git worktree add .worktrees/feature-auth feature-auth
  → Preparing worktree (new branch 'feature-auth')
  → Checking out files: 100% done
$ git worktree list
  → /home/user/project [main]
  → /home/user/project/.worktrees/feature-auth [feature-auth]

Phase 3 - VERIFY
$ git -C .worktrees/feature-auth status
  → On branch feature-auth, nothing to commit, working tree clean ✓

Phase 4 - CHAIN TO PLANNING
→ Invoke dev-workflow:writing-plans
→ Create implementation plan for authentication feature
→ Plan executes in isolated worktree (use git -C .worktrees/feature-auth ...)
→ No conflicts with main workspace

Phase 5 - CLEANUP (after merge)
$ git worktree remove .worktrees/feature-auth
$ git branch -d feature-auth
$ git worktree list
  → /home/user/project [main]
  → Worktree cleaned up ✓
```

## Directory Naming Examples

```
Main repo: /home/user/workspace/my-app
Worktrees (inside .worktrees/):
  .worktrees/feature-auth      → Authentication feature
  .worktrees/fix-login-bug     → Bug fix branch
  .worktrees/refactor-api      → Refactoring work
  .worktrees/add-tests         → Test additions

Main repo: /home/user/workspace/claude-code-workflows
Worktrees (inside .worktrees/):
  .worktrees/context-recovery
  .worktrees/pr-merge-improvements
  .worktrees/new-skill
```

## Troubleshooting

### "Branch already exists"

```bash
# Check where branch exists
git branch -a | grep branch-name

# If local, use different name or delete old branch
git branch -d branch-name

# If remote, fetch and use different name
git fetch origin
```

### "Worktree already exists"

```bash
# List worktrees
git worktree list

# Remove if stale
git worktree remove .worktrees/branch-name

# Or prune all stale worktrees
git worktree prune
```

### "Directory already exists"

```bash
# Check if directory is a worktree
git worktree list | grep branch-name

# If not a worktree, remove or use different name
rm -rf .worktrees/branch-name
```

### "Cannot remove worktree with uncommitted changes"

```bash
# Option 1: Commit or stash changes in the worktree
git -C .worktrees/branch-name add .
git -C .worktrees/branch-name commit -m "WIP: save work"

# Option 2: Force remove (loses changes)
git worktree remove --force .worktrees/branch-name
```
