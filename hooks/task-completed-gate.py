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
import sys
import re


# Patterns indicating an implementation task (case-insensitive)
IMPL_PATTERNS = [
    r'\b(implement|create|add|build|write|update|refactor|fix|migrate)\b',
    r'\btask\s+\d+\.\d+\b',
]

# Patterns indicating a review/meta task (not subject to review gate)
REVIEW_PATTERNS = [
    r'\b(review|verify|check|inspect|audit|approve)\b',
    r'\bready\s+for\s+review\b',
    r'\breview(ed|er)\b',
    r'\b(meta|setup|cleanup|housekeeping)\b',
]

# Patterns indicating task has already been reviewed
REVIEWED_INDICATORS = [
    r'\breviewed\b',
    r'\bapproved\b',
    r'\bPASS\b',
    r'\breview\s+passed\b',
]


def is_implementation_task(subject, description):
    """Check if the task looks like an implementation task."""
    text = f"{subject} {description}".lower()

    # Check if it matches review/meta patterns first (exclude from gate)
    for pattern in REVIEW_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # Check if it matches implementation patterns
    for pattern in IMPL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def is_already_reviewed(subject, description):
    """Check if the task shows signs of having been reviewed."""
    text = f"{subject} {description}".lower()

    for pattern in REVIEWED_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def main():
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
