#!/usr/bin/env python3
"""Unit tests for inject-current-time hook helpers.

Run with: python3 -m unittest hooks/test_inject_current_time.py

Stdlib only — no pytest required.
"""
import datetime
import importlib.util
import os
import unittest
from unittest.mock import patch


_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "inject_current_time", os.path.join(_HERE, "inject-current-time.py")
)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _aware(year, month, day, hour, minute=0, tz="EST"):
    """Build an aware datetime with a fixed tzname for stable assertions."""
    offset = datetime.timezone(datetime.timedelta(hours=-5), name=tz)
    return datetime.datetime(year, month, day, hour, minute, tzinfo=offset)


class RenderTests(unittest.TestCase):
    """End-to-end of the bracketed note produced for a given datetime."""

    def _render_clean_env(self, now, env=None):
        with patch.dict(os.environ, env or {}, clear=True):
            return mod.render(now)

    def test_default_output_is_just_bracketed_time(self):
        now = _aware(2026, 5, 26, 14, 4)
        self.assertEqual(
            self._render_clean_env(now),
            "[current time: 2026-05-26 14:04 EST]",
        )

    def test_late_hour_suffix_requires_both_env_vars(self):
        now = _aware(2026, 5, 26, 3, 0)
        bare = "[current time: 2026-05-26 03:00 EST]"
        # Only start set — must not fire (incomplete config)
        self.assertEqual(
            self._render_clean_env(now, {"CLAUDE_TIME_LATE_START": "2"}),
            bare,
        )
        # Only end set (symmetric case) — must not fire either
        self.assertEqual(
            self._render_clean_env(now, {"CLAUDE_TIME_LATE_END": "5"}),
            bare,
        )
        # Both set, in window — fires
        self.assertIn(
            "past late-hour wrap-up cutoff",
            self._render_clean_env(
                now, {"CLAUDE_TIME_LATE_START": "2", "CLAUDE_TIME_LATE_END": "5"}
            ),
        )

    def test_late_hour_window_is_half_open(self):
        env = {"CLAUDE_TIME_LATE_START": "2", "CLAUDE_TIME_LATE_END": "5"}
        # Start hour: included
        self.assertIn(
            "wrap-up", self._render_clean_env(_aware(2026, 5, 26, 2, 0), env)
        )
        # End hour: excluded
        self.assertNotIn(
            "wrap-up", self._render_clean_env(_aware(2026, 5, 26, 5, 0), env)
        )
        # Outside: excluded
        self.assertNotIn(
            "wrap-up", self._render_clean_env(_aware(2026, 5, 26, 14, 0), env)
        )

    def test_late_hour_env_var_non_int_is_ignored(self):
        env = {"CLAUDE_TIME_LATE_START": "two", "CLAUDE_TIME_LATE_END": "5"}
        self.assertNotIn(
            "wrap-up", self._render_clean_env(_aware(2026, 5, 26, 3, 0), env)
        )

    def test_equal_start_and_end_is_empty_window(self):
        # Half-open [3, 3) — deliberately empty, not a single-hour window
        env = {"CLAUDE_TIME_LATE_START": "3", "CLAUDE_TIME_LATE_END": "3"}
        for hour in (2, 3, 4):
            with self.subTest(hour=hour):
                self.assertNotIn(
                    "wrap-up",
                    self._render_clean_env(_aware(2026, 5, 26, hour, 0), env),
                )

    def test_midnight_spanning_window_fires_correctly(self):
        # "Late night" config: 22:00 → 03:00 spans midnight
        env = {"CLAUDE_TIME_LATE_START": "22", "CLAUDE_TIME_LATE_END": "3"}
        for hour in (22, 23, 0, 1, 2):
            with self.subTest(hour=hour):
                self.assertIn(
                    "wrap-up",
                    self._render_clean_env(_aware(2026, 5, 26, hour, 0), env),
                )
        for hour in (3, 14, 21):
            with self.subTest(hour=hour):
                self.assertNotIn(
                    "wrap-up",
                    self._render_clean_env(_aware(2026, 5, 26, hour, 0), env),
                )

    def test_dst_suffix_off_by_default(self):
        # 2026 spring forward is March 8 — render on the day with NO env var
        self.assertNotIn(
            "DST", self._render_clean_env(_aware(2026, 3, 8, 10, 0))
        )

    def test_dst_suffix_us_region_fires_pre_2am_on_transition_day(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # 1:30 AM on transition day — change is "tonight" (still upcoming)
        out = self._render_clean_env(_aware(2026, 3, 8, 1, 30), env)
        self.assertIn("DST spring-forward TONIGHT", out)

    def test_dst_suffix_post_2am_on_transition_day_is_past_tense(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # 10 AM on spring-forward day — clocks already changed at 2 AM
        out = self._render_clean_env(_aware(2026, 3, 8, 10, 0), env)
        self.assertIn("DST spring-forward happened earlier today", out)
        self.assertNotIn("TONIGHT", out)

    def test_dst_fall_back_pre_2am_on_transition_day(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # Nov 1 2026 is the 1st Sunday — fall back transition day
        out = self._render_clean_env(_aware(2026, 11, 1, 1, 30), env)
        self.assertIn("DST fall-back TONIGHT", out)

    def test_dst_fall_back_post_2am_on_transition_day(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        out = self._render_clean_env(_aware(2026, 11, 1, 10, 0), env)
        self.assertIn("DST fall-back happened earlier today", out)

    def test_dst_pre_transition_window_boundary(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # 3 days before spring-forward (March 8) = March 5 — inside window
        self.assertIn(
            "DST spring-forward in 3d",
            self._render_clean_env(_aware(2026, 3, 5, 10, 0), env),
        )
        # 4 days before = March 4 — outside window, silent
        self.assertNotIn(
            "DST", self._render_clean_env(_aware(2026, 3, 4, 10, 0), env)
        )

    def test_dst_post_transition_window_boundary(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # 1 day after spring-forward — should fire with "started Nd ago"
        self.assertIn(
            "DST started 1d ago",
            self._render_clean_env(_aware(2026, 3, 9, 10, 0), env),
        )
        # 3 days after — last day of window
        self.assertIn(
            "DST started 3d ago",
            self._render_clean_env(_aware(2026, 3, 11, 10, 0), env),
        )
        # 4 days after — outside window, silent
        self.assertNotIn(
            "DST", self._render_clean_env(_aware(2026, 3, 12, 10, 0), env)
        )

    def test_dst_suffix_outside_window_silent(self):
        env = {"CLAUDE_TIME_DST_REGION": "us"}
        # July 1 is months from any transition
        self.assertNotIn(
            "DST", self._render_clean_env(_aware(2026, 7, 1, 10, 0), env)
        )

    def test_dst_region_case_insensitive(self):
        env = {"CLAUDE_TIME_DST_REGION": "US"}
        self.assertIn(
            "DST", self._render_clean_env(_aware(2026, 3, 8, 10, 0), env)
        )

    def test_dst_region_unrecognized_value_is_silent(self):
        env = {"CLAUDE_TIME_DST_REGION": "eu"}
        self.assertNotIn(
            "DST", self._render_clean_env(_aware(2026, 3, 8, 10, 0), env)
        )

    def test_both_suffixes_compose_with_semicolon(self):
        env = {
            "CLAUDE_TIME_LATE_START": "2",
            "CLAUDE_TIME_LATE_END": "5",
            "CLAUDE_TIME_DST_REGION": "us",
        }
        # Day before spring-forward, in the late window — both suffixes fire
        # without the transition-time interaction
        out = self._render_clean_env(_aware(2026, 3, 7, 3, 15), env)
        self.assertIn("past late-hour wrap-up cutoff", out)
        self.assertIn("DST spring-forward in 1d", out)
        self.assertEqual(out.count(";"), 1)


class DstTransitionTests(unittest.TestCase):
    """The date math underlying the DST suffix."""

    def test_spring_forward_2026(self):
        # 2nd Sunday of March 2026 — should be March 8
        transition, kind, _ = mod.closest_us_dst_transition(
            datetime.date(2026, 3, 1)
        )
        self.assertEqual(transition, datetime.date(2026, 3, 8))
        self.assertEqual(kind, "spring forward")

    def test_fall_back_2026(self):
        # 1st Sunday of November 2026 — should be November 1
        transition, kind, _ = mod.closest_us_dst_transition(
            datetime.date(2026, 10, 28)
        )
        self.assertEqual(transition, datetime.date(2026, 11, 1))
        self.assertEqual(kind, "fall back")

    def test_picks_just_passed_transition_when_closer(self):
        # 2 days after spring forward: closest transition should still be
        # the just-passed one, not the future fall-back
        transition, kind, days_to = mod.closest_us_dst_transition(
            datetime.date(2026, 3, 10)
        )
        self.assertEqual(kind, "spring forward")
        self.assertEqual(days_to, -2)


if __name__ == "__main__":
    unittest.main()
