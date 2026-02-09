#!/usr/bin/env python3
"""
Task Completed Gate Hook - TaskCompleted hook for agent team development.
Prevents implementation tasks from being marked complete before review.

When a teammate marks a task as complete, this hook checks whether
the task appears to be an implementation task that hasn't been reviewed.
If so, it blocks completion with a message directing review.

Usage: Configure in hooks/hooks.json as a TaskCompleted hook.
"""
import json
import os
import sys
import re


# Patterns indicating an implementation task (matched against lowercased text)
IMPL_PATTERNS = [
    r'\b(implement|create|add|build|write|update|refactor|fix|migrate)\b',
    r'\btask\s+\d+\.\d+\b',
]

# Patterns indicating the task is primarily a review/meta task (not subject to review gate)
# These are narrow to avoid false negatives on implementation tasks containing "check" etc.
REVIEW_PATTERNS = [
    r'^review\b',
    r'\breview\s+(this|the|task|code|changes|implementation)\b',
    r'\bready\s+for\s+review\b',
    r'^(meta|setup|cleanup|housekeeping)\b',
    r'\b(spec|quality|staff)\s+review\b',
]

# Patterns indicating task has already been reviewed (matched against lowercased text)
REVIEWED_INDICATORS = [
    r'\breviewed\b',
    r'\bapproved\b',
    r'\bpass\b',
    r'\breview\s+passed\b',
]


def is_implementation_task(subject, description):
    """Check if the task looks like an implementation task."""
    text = f"{subject} {description}".lower()

    # Check if subject primarily matches review/meta patterns (exclude from gate)
    subject_lower = subject.lower()
    for pattern in REVIEW_PATTERNS:
        if re.search(pattern, subject_lower):
            return False

    # Check if it matches implementation patterns
    for pattern in IMPL_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


def is_already_reviewed(subject, description):
    """Check if the task shows signs of having been reviewed."""
    text = f"{subject} {description}".lower()

    for pattern in REVIEWED_INDICATORS:
        if re.search(pattern, text):
            return True

    return False


def main():
    # Only enforce review gate when agent teams are active
    if not os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"):
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        # Graceful fallback - don't block if we can't parse input
        sys.exit(0)

    # Extract task information from the hook payload
    tool_input = input_data.get("tool_input", {})
    subject = tool_input.get("subject", "")
    description = tool_input.get("description", "")

    # If we can't determine task details, don't block
    if not subject and not description:
        sys.exit(0)

    # Check if this is an implementation task
    if not is_implementation_task(subject, description):
        sys.exit(0)

    # Check if it's already been reviewed
    if is_already_reviewed(subject, description):
        sys.exit(0)

    # Block completion - implementation task needs review first
    print(
        "Task requires review before completion. "
        "Reviewer: please review this task before marking it complete.",
        file=sys.stderr
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
