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
- Executing implementation plans with `dev-workflow:agent-team-development` (or `subagent-driven-development` fallback)
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

**Create worktree with smart directory naming:**

```bash
# Sibling directory pattern: ../repo-feature-name
# Example: claude-code-workflows → ../claude-code-workflows-feature-auth

cd /home/tbaker/workspace/claude-code-workflows
git worktree add ../claude-code-workflows-feature-auth feature-auth
```

**Directory naming convention:**
- Pattern: `../REPO_NAME-BRANCH_NAME`
- Example: `../claude-code-workflows-context-recovery`
- Keeps worktrees organized as siblings to main repo
- Easy to identify and clean up later

**Checkpoint:** Worktree created. Directory exists.

### Phase 3: Navigate and Verify

**Navigate to worktree:**

```bash
cd ../claude-code-workflows-feature-auth
```

**Verify worktree state:**

```bash
# Confirm branch and clean state
git status

# Verify worktree list
git worktree list
```

**Checkpoint:** In worktree directory. Branch is correct. State is clean.

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

1. **Return to main repo:**

```bash
cd /home/tbaker/workspace/claude-code-workflows
```

2. **Remove worktree:**

```bash
# Remove worktree directory and unregister it
git worktree remove ../claude-code-workflows-feature-auth

# Or if directory was manually deleted:
git worktree prune
```

3. **Delete branch (if merged):**

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
git worktree add ../repo-branch-name branch-name

# Create worktree for existing branch
git worktree add ../repo-existing-branch existing-branch

# Create worktree and new branch from specific commit
git worktree add -b new-branch ../repo-new-branch abc123
```

### Managing Worktrees

```bash
# List all worktrees
git worktree list

# Remove specific worktree
git worktree remove ../repo-branch-name

# Remove worktree (if already deleted manually)
git worktree prune

# Remove worktree with uncommitted changes (force)
git worktree remove --force ../repo-branch-name
```

### Working in Worktrees

```bash
# Navigate to worktree
cd ../repo-branch-name

# All git commands work normally
git status
git add .
git commit -m "feat: implement feature"
git push origin branch-name

# Return to main repo
cd /home/tbaker/workspace/claude-code-workflows
```

## Process Flow

### Starting Feature Work with Worktree

1. **Verify main repo state** - `git status` shows clean
2. **Check branch availability** - `git branch -a | grep feature-name` is empty
3. **Create feature branch** - `git branch feature-name`
4. **Create worktree** - `git worktree add ../repo-feature-name feature-name`
5. **Navigate to worktree** - `cd ../repo-feature-name`
6. **Verify worktree** - `git status`, `git worktree list`
7. **Chain to writing-plans** - Ready for implementation planning

### Verification at Each Phase

- After SAFETY CHECKS: Main clean, branch name available
- After CREATE: Worktree exists, branch created
- After NAVIGATE: In worktree directory, correct branch
- After CHAIN: Implementation plan can execute in isolation

## Integration with Other Skills

**Chains to `dev-workflow:writing-plans`:**
- Set up worktree first for isolated workspace
- Then invoke writing-plans in the worktree context
- Implementation plan executes in clean, isolated environment

**Works with `dev-workflow:agent-team-development`:**
- Agent teams create per-implementer worktrees automatically
- Provides true parallel execution with worktree isolation
- Reviewer and implementers communicate via mailbox

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
❌ Creating worktree in subdirectory of main repo
❌ Forgetting to navigate to worktree after creation
❌ Leaving worktrees around after feature is merged
❌ Using worktree for quick branch switches (just use `git switch`)
❌ Creating nested worktrees

## Success Criteria

✅ Main repo state is clean before worktree creation
✅ Branch name is unique (doesn't exist locally or remotely)
✅ Worktree created in sibling directory with clear naming
✅ Successfully navigated to worktree directory
✅ Worktree list shows both main and new worktree
✅ Implementation plan chains after worktree setup
✅ Cleanup performed after feature merge/completion

## Example Flow

```
SCENARIO: Implementing new authentication feature with parallel agents

Phase 1 - SAFETY CHECKS
$ cd /home/tbaker/workspace/claude-code-workflows
$ git status
  → On branch main, working tree clean ✓
$ git branch -a | grep feature-auth
  → No output, branch name available ✓

Phase 2 - CREATE
$ git branch feature-auth
$ git worktree add ../claude-code-workflows-feature-auth feature-auth
  → Preparing worktree (new branch 'feature-auth')
  → Checking out files: 100% done
$ git worktree list
  → /home/tbaker/workspace/claude-code-workflows [main]
  → /home/tbaker/workspace/claude-code-workflows-feature-auth [feature-auth]

Phase 3 - NAVIGATE
$ cd ../claude-code-workflows-feature-auth
$ git status
  → On branch feature-auth, nothing to commit, working tree clean ✓

Phase 4 - CHAIN TO PLANNING
→ Invoke dev-workflow:writing-plans
→ Create implementation plan for authentication feature
→ Plan executes in isolated worktree
→ No conflicts with main workspace

Phase 5 - CLEANUP (after merge)
$ cd /home/tbaker/workspace/claude-code-workflows
$ git worktree remove ../claude-code-workflows-feature-auth
$ git branch -d feature-auth
$ git worktree list
  → /home/tbaker/workspace/claude-code-workflows [main]
  → Worktree cleaned up ✓
```

## Directory Naming Examples

```
Main repo: /home/tbaker/workspace/my-app
Worktrees:
  ../my-app-feature-auth      → Authentication feature
  ../my-app-fix-login-bug     → Bug fix branch
  ../my-app-refactor-api      → Refactoring work
  ../my-app-add-tests         → Test additions

Main repo: /home/tbaker/workspace/claude-code-workflows
Worktrees:
  ../claude-code-workflows-context-recovery
  ../claude-code-workflows-pr-merge-improvements
  ../claude-code-workflows-new-skill
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
git worktree remove ../repo-branch-name

# Or prune all stale worktrees
git worktree prune
```

### "Directory already exists"

```bash
# Check if directory is a worktree
git worktree list | grep directory-name

# If not a worktree, remove or use different name
rm -rf ../directory-name
```

### "Cannot remove worktree with uncommitted changes"

```bash
# Option 1: Commit or stash changes
cd ../repo-branch-name
git add .
git commit -m "WIP: save work"

# Option 2: Force remove (loses changes)
cd /home/tbaker/workspace/main-repo
git worktree remove --force ../repo-branch-name
```
