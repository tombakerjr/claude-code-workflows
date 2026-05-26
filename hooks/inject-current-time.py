#!/usr/bin/env python3
"""
inject-current-time — UserPromptSubmit hook

Emits a small bracketed system note on every user message with the current
local time. Closes the wall-clock-awareness gap: Claude's training data
has a fixed cutoff, so without an injection like this it cannot
distinguish "this morning" from "six months ago," reason about whether
a release / deploy / changelog entry is recent, or judge urgency.

Output format:
    [current time: 2026-05-26 14:04 EDT]
    [current time: 2026-03-08 03:15 EST — past late-hour wrap-up cutoff]
    [current time: 2026-03-08 03:15 EST — past late-hour wrap-up cutoff;
        DST spring-forward TONIGHT — clocks jump 2 AM → 3 AM]

Cost: ~12-25 tokens per turn depending on which suffixes fire.

Optional suffixes (off by default — opt in via env vars):

    CLAUDE_TIME_LATE_START=2   start hour (24h) of "wrap up" window
    CLAUDE_TIME_LATE_END=5     end hour (exclusive) of the window

When BOTH are set to integers and the current hour falls in
[LATE_START, LATE_END), the note gets a "past late-hour wrap-up cutoff"
suffix. Useful as a self-care nudge for late-night coders.

    CLAUDE_TIME_DST_REGION=us  enable US DST transition nudges

When set to "us", the note gets a transition reminder within ±3 days of
the second-Sunday-in-March / first-Sunday-in-November US DST changes.
Only "us" is implemented; non-US regions emit no DST suffix.
"""
import datetime
import os
import sys


DST_WINDOW_DAYS = 3


def _env_int(name):
    """Return env var as int, or None if unset / not parseable."""
    raw = os.environ.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def late_hour_suffix(now):
    """Suffix when inside the user-configured late-hour window. Off unless
    both CLAUDE_TIME_LATE_START and CLAUDE_TIME_LATE_END are set.

    The window is half-open `[start, end)` — `start` hour fires, `end`
    hour does not. So `start == end` is a deliberately empty window
    (no hour matches), not a single-hour window. For "fire at hour N
    only" set `START=N END=N+1`. For "fire at hour N and onward through
    M (inclusive)" set `START=N END=M+1`.

    Supports midnight-spanning windows (start > end), so the natural
    "late night" config CLAUDE_TIME_LATE_START=22 CLAUDE_TIME_LATE_END=3
    fires at 22:00, 23:00, 00:00, 01:00, 02:00.
    """
    start = _env_int("CLAUDE_TIME_LATE_START")
    end = _env_int("CLAUDE_TIME_LATE_END")
    if start is None or end is None:
        return ""
    h = now.hour
    if start <= end:
        in_window = start <= h < end
    else:
        in_window = h >= start or h < end
    return "past late-hour wrap-up cutoff" if in_window else ""


def closest_us_dst_transition(today_date):
    """Return (transition_date, kind, days_to) for the US DST transition
    closest to today_date — past or future.

    kind is "spring forward" (clocks +1h, lose an hour of sleep) or
    "fall back" (clocks -1h, gain an hour). Uses the US rule: 2nd
    Sunday of March / 1st Sunday of November.

    Considering the prior, current, and next years (three in total)
    ensures we don't lose the just-passed transition case when computing
    days_to near a year boundary.
    """
    candidates = []
    for year in (today_date.year - 1, today_date.year, today_date.year + 1):
        march_1 = datetime.date(year, 3, 1)
        spring = march_1 + datetime.timedelta(
            days=((6 - march_1.weekday()) % 7) + 7
        )
        nov_1 = datetime.date(year, 11, 1)
        fall = nov_1 + datetime.timedelta(days=(6 - nov_1.weekday()) % 7)
        candidates.append((spring, "spring forward"))
        candidates.append((fall, "fall back"))

    transition, kind = min(
        candidates, key=lambda t: abs((t[0] - today_date).days)
    )
    return transition, kind, (transition - today_date).days


def dst_suffix(now):
    """US DST nudge string, within ±DST_WINDOW_DAYS of the closest
    transition. Off unless CLAUDE_TIME_DST_REGION=us.

    Takes the full `now` datetime (not just date) because on transition
    day itself the message needs to flip from future-tense ("TONIGHT")
    to past-tense once 2 AM local has passed.
    """
    if os.environ.get("CLAUDE_TIME_DST_REGION", "").lower() != "us":
        return ""

    transition, kind, days_to = closest_us_dst_transition(now.date())
    if abs(days_to) > DST_WINDOW_DAYS:
        return ""

    # On the transition day, after 2 AM local the change has already
    # happened — treat it as same-day-past rather than upcoming.
    transition_passed = days_to == 0 and now.hour >= 2

    if kind == "spring forward":
        if days_to > 0:
            return (
                f"DST spring-forward in {days_to}d — clocks ahead 1h Sunday "
                f"at 2 AM, aim to wind down a little earlier each night"
            )
        if days_to == 0 and not transition_passed:
            return "DST spring-forward TONIGHT — clocks jump 2 AM → 3 AM"
        if transition_passed:
            return (
                "DST spring-forward happened earlier today — clocks already "
                "at +1h, body adjusting"
            )
        return (
            f"DST started {-days_to}d ago — body still adjusting, expect "
            f"shorter / lighter sleep for a few days"
        )

    # fall back
    if days_to > 0:
        return (
            f"DST fall-back in {days_to}d — clocks back 1h Sunday at 2 AM, "
            f"bonus hour of sleep available (use it)"
        )
    if days_to == 0 and not transition_passed:
        return "DST fall-back TONIGHT — clocks roll 2 AM → 1 AM"
    if transition_passed:
        return (
            "DST fall-back happened earlier today — clocks already at -1h, "
            "earlier sunsets from here"
        )
    return (
        f"DST ended {-days_to}d ago — earlier sunsets, body still adjusting"
    )


def render(now):
    """Build the full bracketed note.

    Not strictly pure — the suffix helpers read CLAUDE_TIME_* env vars —
    but easy to unit-test by patching `os.environ` (see test file).
    """
    tz_name = now.tzname() or ""
    time_str = now.strftime("%Y-%m-%d %H:%M") + (f" {tz_name}" if tz_name else "")

    suffixes = []
    late = late_hour_suffix(now)
    if late:
        suffixes.append(late)
    dst = dst_suffix(now)
    if dst:
        suffixes.append(dst)

    suffix_text = (" — " + "; ".join(suffixes)) if suffixes else ""
    return f"[current time: {time_str}{suffix_text}]"


def main():
    # Drain stdin so Claude Code's write to the hook does not race a closed
    # pipe. UserPromptSubmit hooks receive a JSON payload; we don't use it,
    # but we still need to consume it. Matches the pattern in git-guard.py
    # and task-completed-gate.py.
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass
    now = datetime.datetime.now().astimezone()
    print(render(now))


if __name__ == "__main__":
    main()
