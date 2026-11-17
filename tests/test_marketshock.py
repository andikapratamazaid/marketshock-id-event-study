#!/usr/bin/env python3
"""Tests for the MarketShock ID event study.

Covers: return mathematics on known inputs, the close-validity rule,
event-window extraction logic, z-scores, rolling volatility, and
integrity checks on the actual processed panel (including proof that
invalid USD/IDR closes were excluded rather than filled).

Run from the project root:
    python3 -m unittest discover -s tests -v
"""

import json
import math
import os
import sys
import unittest

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "analysis"))

import run_analysis as ra  # noqa: E402

PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed", "market_daily.csv")
RESULTS = os.path.join(PROJECT_ROOT, "output", "analysis_results.json")
RAW_USDIDR = os.path.join(PROJECT_ROOT, "data", "raw", "usdidr.csv")


class TestReturnMath(unittest.TestCase):
    def test_daily_returns_known_inputs(self):
        r = ra.daily_returns([100.0, 110.0, 99.0])
        self.assertTrue(math.isnan(r.iloc[0]))
        self.assertAlmostEqual(r.iloc[1], 0.10, places=10)
        self.assertAlmostEqual(r.iloc[2], -0.10, places=10)

    def test_daily_returns_flat_series(self):
        r = ra.daily_returns([50.0, 50.0, 50.0])
        self.assertAlmostEqual(r.iloc[1], 0.0, places=12)
        self.assertAlmostEqual(r.iloc[2], 0.0, places=12)

    def test_cumulative_return(self):
        self.assertAlmostEqual(ra.cumulative_return([100.0, 110.0]), 0.10,
                               places=10)
        self.assertAlmostEqual(ra.cumulative_return([200.0, 150.0]), -0.25,
                               places=10)

    def test_cumulative_return_insufficient_data(self):
        self.assertIsNone(ra.cumulative_return([100.0]))
        self.assertIsNone(ra.cumulative_return([]))


class TestValidityRule(unittest.TestCase):
    def test_close_inside_range_is_valid(self):
        self.assertTrue(ra.is_valid_close(105.0, 100.0, 110.0))
        self.assertTrue(ra.is_valid_close(100.0, 100.0, 110.0))
        self.assertTrue(ra.is_valid_close(110.0, 100.0, 110.0))

    def test_close_outside_range_is_invalid(self):
        # The actual 12 Nov 2026 USD/IDR tick from the source feed.
        self.assertFalse(ra.is_valid_close(17489.5, 18140.0, 18260.599609))
        self.assertFalse(ra.is_valid_close(120.0, 100.0, 110.0))

    def test_missing_values_are_invalid(self):
        self.assertFalse(ra.is_valid_close(None, 100.0, 110.0))
        self.assertFalse(ra.is_valid_close(float("nan"), 100.0, 110.0))
        self.assertFalse(ra.is_valid_close(105.0, None, 110.0))


class TestEventWindow(unittest.TestCase):
    def setUp(self):
        # 21 trading days, price grows exactly 1 percent per day.
        self.dates = ["2026-01-%02d" % d for d in range(1, 22)]
        self.closes = [100.0 * (1.01 ** i) for i in range(21)]
        r = ra.daily_returns(self.closes)
        self.changes = [None if pd.isna(v) else float(v) for v in r]

    def test_event_position(self):
        self.assertEqual(ra.event_position(self.dates, "2026-01-11"), 10)
        self.assertIsNone(ra.event_position(self.dates, "2026-02-01"))

    def test_event_position_with_calendar_gap(self):
        # Observations skip 2026-01-11 (a weekend-style gap): the event
        # must anchor to the next available observation, 2026-01-12.
        gapped = [d for d in self.dates if d != "2026-01-11"]
        self.assertEqual(ra.event_position(gapped, "2026-01-11"),
                         gapped.index("2026-01-12"))

    def test_window_extraction_middle_event(self):
        st = ra.event_window_stats(self.dates, self.closes, self.changes,
                                   "2026-01-11", pre=5, post=5)
        self.assertTrue(st["available"])
        self.assertTrue(st["on_exact_date"])
        self.assertEqual(st["window_start_date"], "2026-01-06")
        self.assertEqual(st["window_end_date"], "2026-01-16")
        self.assertFalse(st["window_truncated"])
        self.assertAlmostEqual(st["event_day_change"], 0.01, places=10)
        # 10 daily steps of 1 percent inside the window.
        self.assertAlmostEqual(st["window_cumulative_change"],
                               1.01 ** 10 - 1.0, places=10)

    def test_window_truncates_at_series_end(self):
        st = ra.event_window_stats(self.dates, self.closes, self.changes,
                                   "2026-01-21", pre=5, post=5)
        self.assertTrue(st["window_truncated"])
        self.assertEqual(st["window_end_date"], "2026-01-21")

    def test_event_after_data_is_unavailable(self):
        st = ra.event_window_stats(self.dates, self.closes, self.changes,
                                   "2026-03-01")
        self.assertFalse(st["available"])


class TestZScoreAndVolatility(unittest.TestCase):
    def test_trailing_zscore_known(self):
        history = [0.0] * 30 + [0.02, -0.02] * 5  # mean 0, std about 0.0116
        z = ra.trailing_zscore(0.02, history)
        self.assertIsNotNone(z)
        self.assertGreater(z, 1.0)

    def test_trailing_zscore_needs_history(self):
        self.assertIsNone(ra.trailing_zscore(0.05, [0.01, 0.02]))

    def test_rolling_volatility_constant_returns(self):
        changes = [None] + [0.01] * 30
        vol = ra.rolling_volatility(changes, window=20)
        self.assertAlmostEqual(float(vol.iloc[-1]), 0.0, places=8)

    def test_rolling_volatility_length_preserved(self):
        changes = [None] + [0.01, -0.01] * 15
        vol = ra.rolling_volatility(changes, window=20)
        self.assertEqual(len(vol), len(changes))


@unittest.skipUnless(os.path.exists(PROCESSED), "processed panel missing")
class TestProcessedPanelIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = pd.read_csv(PROCESSED, dtype={"date": str})
        cls.by_date = cls.panel.set_index("date")

    def test_expected_columns(self):
        self.assertEqual(
            list(self.panel.columns),
            ["date", "ihsg_close", "usdidr_close", "eido_close",
             "dxy_close", "us10y_yield_pct", "usdidr_close_valid"])

    def test_dates_sorted_and_unique(self):
        dates = self.panel["date"].tolist()
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))

    def test_closes_positive_where_present(self):
        for col in ("ihsg_close", "usdidr_close", "eido_close", "dxy_close",
                    "us10y_yield_pct"):
            vals = self.panel[col].dropna()
            self.assertTrue((vals > 0).all(), col)

    def test_invalid_usdidr_event_closes_excluded_not_filled(self):
        for d in ("2026-11-12", "2026-11-13"):
            self.assertTrue(pd.isna(self.by_date.loc[d, "usdidr_close"]), d)
            # pandas parses the True/False column back as booleans.
            self.assertEqual(bool(self.by_date.loc[d, "usdidr_close_valid"]),
                             False)
        # Neighbouring valid closes are present with their true values.
        self.assertEqual(self.by_date.loc["2026-11-11", "usdidr_close"],
                         18140.0)
        self.assertAlmostEqual(
            self.by_date.loc["2026-11-16", "usdidr_close"],
            18222.400391, places=4)

    def test_no_forward_fill_across_missing_eido_day(self):
        # EIDO has no 2026-11-17 observation in the raw download; the
        # panel row exists (other series traded) and must stay empty.
        self.assertTrue(pd.isna(self.by_date.loc["2026-11-17", "eido_close"]))
        self.assertFalse(pd.isna(self.by_date.loc["2026-11-17", "ihsg_close"]))

    def test_invalid_flag_count_matches_raw_feed(self):
        raw = pd.read_csv(RAW_USDIDR, dtype={"date": str})
        raw_invalid = 0
        for _, row in raw.iterrows():
            if not ra.is_valid_close(row["close"], row["low"], row["high"]):
                raw_invalid += 1
        panel_invalid = int(
            (self.panel["usdidr_close_valid"] == False).sum())  # noqa: E712
        self.assertEqual(panel_invalid, raw_invalid)
        self.assertEqual(raw_invalid, 27)


@unittest.skipUnless(os.path.exists(RESULTS), "results json missing")
class TestResultsConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(RESULTS) as fh:
            cls.r = json.load(fh)

    def test_crosscheck_against_reported_ihsg(self):
        cc = self.r["crosscheck_ihsg_2026_11_12"]
        self.assertAlmostEqual(cc["fetched_close"], 5250.90, delta=0.5)
        self.assertAlmostEqual(cc["fetched_daily_return_pct"], 2.66,
                               delta=0.05)

    def test_event_day_decomposition_matches_crosscheck(self):
        day = self.r["global_investor_decomposition"]["event_day_2026_11_12"]
        cc = self.r["crosscheck_ihsg_2026_11_12"]
        self.assertAlmostEqual(day["ihsg_return_pct"],
                               cc["fetched_daily_return_pct"], places=6)
        # The honest gap: no USD/IDR event-day return may be reported.
        self.assertIsNone(day["usdidr_return_pct"])

    def test_residual_arithmetic(self):
        b = self.r["global_investor_decomposition"]["bracket_11nov_to_16nov"]
        self.assertAlmostEqual(
            b["usdidr_residual_vs_dxy_pp"],
            round(b["usdidr_return_pct"] - b["dxy_return_pct"], 4),
            places=6)


if __name__ == "__main__":
    unittest.main()
