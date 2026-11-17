#!/usr/bin/env python3
"""Run the MarketShock ID event study analysis.

Reads the raw downloaded series in data/raw/, applies a documented
data-quality rule (a close is valid only if it lies inside the day's
own high-low range; invalid closes are treated as missing and are
NEVER replaced or interpolated), builds the merged daily panel, and
computes event-window statistics, rolling volatility, and the global
investor decomposition.

Outputs:
    data/processed/market_daily.csv
    output/analysis_results.json
    charts/*.png

The core math functions are importable so tests/test_marketshock.py
can verify them on known inputs.
"""

import json
import math
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "market_daily.csv")
RESULTS_PATH = os.path.join(PROJECT_ROOT, "output", "analysis_results.json")
CHART_DIR = os.path.join(PROJECT_ROOT, "charts")

SERIES_FILES = {
    "ihsg": "ihsg.csv",
    "usdidr": "usdidr.csv",
    "eido": "eido.csv",
    "dxy": "dxy.csv",
    "us10y": "us10y.csv",
}

PANEL_COLUMNS = {
    "ihsg": "ihsg_close",
    "usdidr": "usdidr_close",
    "eido": "eido_close",
    "dxy": "dxy_close",
    "us10y": "us10y_yield_pct",
}

EVENTS = [
    {"id": "hoax_factcheck_marker", "date": "2026-09-30",
     "label": "Hoax wave fact-check marker (Kompas.com, 30 Sep 2026)",
     "kind": "marker"},
    {"id": "ma_decision", "date": "2026-10-30",
     "label": "Supreme Court cassation decision (30 Oct 2026)",
     "kind": "event"},
    {"id": "hmp_proposal", "date": "2026-11-11",
     "label": "HMP proposal and letter revocation (11 Nov 2026)",
     "kind": "event"},
    {"id": "resignation", "date": "2026-11-12",
     "label": "Vice President resigns (12 Nov 2026, MAIN EVENT)",
     "kind": "main_event"},
]

MAIN_EVENT_DATE = "2026-11-12"
PRE_EVENT_CLOSE_DATE = "2026-11-11"
FIRST_POST_EVENT_VALID_DATE = "2026-11-16"
DATA_END = "2026-11-17"


# ---------------------------------------------------------------------------
# Core math (imported by the test suite)
# ---------------------------------------------------------------------------

def is_valid_close(close, low, high):
    """A close is valid only if it lies inside the day's high-low range."""
    if close is None or low is None or high is None:
        return False
    try:
        close = float(close)
        low = float(low)
        high = float(high)
    except (TypeError, ValueError):
        return False
    if math.isnan(close) or math.isnan(low) or math.isnan(high):
        return False
    return low - 1e-9 <= close <= high + 1e-9


def daily_returns(closes):
    """Simple daily returns of a close series, aligned to the input index.

    The first observation has no return (NaN). Computed only between
    consecutive available observations; gaps are not filled.
    """
    closes = pd.Series(closes, dtype=float)
    return closes / closes.shift(1) - 1.0


def cumulative_return(closes):
    """Total return from the first to the last close in the sequence."""
    closes = [float(c) for c in closes if c is not None and not math.isnan(float(c))]
    if len(closes) < 2:
        return None
    return closes[-1] / closes[0] - 1.0


def event_position(dates, event_date):
    """Position of the first observation date on or after event_date.

    dates: sorted list of 'YYYY-MM-DD' strings. Returns None if the
    event is after the last observation.
    """
    for i, d in enumerate(dates):
        if d >= event_date:
            return i
    return None


def trailing_zscore(value, history, min_obs=20):
    """Z-score of value against the trailing history (sample std)."""
    hist = [float(h) for h in history if h is not None and not math.isnan(float(h))]
    if value is None or len(hist) < min_obs:
        return None
    mean = sum(hist) / len(hist)
    var = sum((h - mean) ** 2 for h in hist) / (len(hist) - 1)
    std = math.sqrt(var)
    if std == 0:
        return None
    return (value - mean) / std


def event_window_stats(dates, closes, changes, event_date, pre=5, post=5,
                       trailing=60):
    """Event-window statistics on one series' own observation calendar.

    dates:   sorted observation dates (only dates with a valid close)
    closes:  matching close levels
    changes: matching daily changes (returns, or yield changes in bps);
             changes[0] is NaN
    Returns a dict with the event-day change, its trailing z-score, and
    the cumulative change across the [event-pre, event+post] window of
    observations, with the actual dates used and a truncation flag.
    """
    n = len(dates)
    pos = event_position(dates, event_date)
    if pos is None:
        return {"available": False, "reason": "event after last observation"}
    on_exact_date = dates[pos] == event_date
    event_change = None
    z = None
    if on_exact_date and pos >= 1:
        event_change = changes[pos]
        z = trailing_zscore(event_change, changes[max(0, pos - trailing):pos])
    start = max(0, pos - pre)
    end = min(n - 1, pos + post)
    truncated = (pos - pre < 0) or (pos + post > n - 1)
    cum = None
    if end > start:
        if all(not math.isnan(c) for c in changes[start + 1:end + 1]):
            prod = 1.0
            for c in changes[start + 1:end + 1]:
                prod *= (1.0 + c)
            cum = prod - 1.0
    return {
        "available": True,
        "event_observation_date": dates[pos],
        "on_exact_date": on_exact_date,
        "event_day_change": event_change,
        "event_day_zscore": z,
        "window_start_date": dates[start],
        "window_end_date": dates[end],
        "window_observations": end - start + 1,
        "window_truncated": truncated,
        "window_cumulative_change": cum,
    }


def rolling_volatility(changes, window=20):
    """Annualized rolling volatility (percent) of daily returns."""
    s = pd.Series(changes, dtype=float)
    return s.rolling(window).std() * math.sqrt(252) * 100.0


# ---------------------------------------------------------------------------
# Data loading and panel construction
# ---------------------------------------------------------------------------

def load_raw(series_id):
    path = os.path.join(RAW_DIR, SERIES_FILES[series_id])
    df = pd.read_csv(path, dtype={"date": str})
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("date").drop_duplicates(subset="date").reset_index(drop=True)
    df["close_valid"] = [
        is_valid_close(c, lo, hi)
        for c, lo, hi in zip(df["close"], df["low"], df["high"])
    ]
    return df


def build_panel():
    """Merged daily panel. Invalid closes become empty (never filled)."""
    frames = {}
    quality = {}
    all_dates = set()
    for series_id in SERIES_FILES:
        df = load_raw(series_id)
        all_dates.update(df["date"].tolist())
        invalid_dates = df.loc[~df["close_valid"], "date"].tolist()
        quality[series_id] = {
            "rows": int(len(df)),
            "invalid_close_dates": invalid_dates,
            "invalid_close_count": int(len(invalid_dates)),
        }
        clean = df.loc[df["close_valid"], ["date", "close"]].copy()
        clean = clean.rename(columns={"close": PANEL_COLUMNS[series_id]})
        frames[series_id] = clean.set_index("date")
    panel = pd.concat(frames.values(), axis=1, join="outer").sort_index()
    # Keep every downloaded date as a panel row, including dates whose
    # only feed row was an invalid USD/IDR tick (for example a Sunday
    # print). Such rows carry no close, only the validity flag, so the
    # exclusion stays visible instead of silently dropping the date.
    panel = panel.reindex(sorted(all_dates))
    panel = panel.reset_index().rename(columns={"index": "date"})
    # Explicit validity flag for USD/IDR so the processed file proves that
    # invalid event-day closes were excluded, not replaced.
    usdidr_raw = load_raw("usdidr")[["date", "close_valid"]]
    panel = panel.merge(usdidr_raw, on="date", how="left")
    panel = panel.rename(columns={"close_valid": "usdidr_close_valid"})
    cols = ["date", "ihsg_close", "usdidr_close", "eido_close", "dxy_close",
            "us10y_yield_pct", "usdidr_close_valid"]
    panel = panel[cols]
    return panel, quality


def series_observations(panel, series_id):
    """(dates, closes) of valid observations for one series, in order."""
    col = PANEL_COLUMNS[series_id]
    sub = panel[["date", col]].dropna(subset=[col])
    return sub["date"].tolist(), sub[col].astype(float).tolist()


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def pct(x):
    return None if x is None else round(x * 100.0, 4)


def analyze(panel):
    results = {"data_end": DATA_END, "main_event_date": MAIN_EVENT_DATE}
    obs = {}
    rets = {}
    for series_id in ("ihsg", "usdidr", "eido", "dxy"):
        dates, closes = series_observations(panel, series_id)
        r = daily_returns(closes)
        obs[series_id] = (dates, closes)
        rets[series_id] = [None if pd.isna(v) else float(v) for v in r]
    # US 10Y: work in yield changes (basis points), not returns.
    ydates, ylevels = series_observations(panel, "us10y")
    ychg = [None]
    for i in range(1, len(ylevels)):
        ychg.append((ylevels[i] - ylevels[i - 1]) * 100.0)

    # --- Cross-check against reported IHSG figures for 12 Nov 2026 ---
    idates, icloses = obs["ihsg"]
    iret = rets["ihsg"]
    pos12 = idates.index(MAIN_EVENT_DATE)
    results["crosscheck_ihsg_2026_11_12"] = {
        "fetched_close": icloses[pos12],
        "reported_close": 5250.90,
        "fetched_daily_return_pct": pct(iret[pos12]),
        "reported_daily_return_pct": 2.66,
        "previous_close": icloses[pos12 - 1],
        "previous_date": idates[pos12 - 1],
    }

    # --- Event windows ---
    events_out = {}
    for ev in EVENTS:
        per_series = {}
        for series_id in ("ihsg", "usdidr", "eido", "dxy"):
            dates, closes = obs[series_id]
            st = event_window_stats(dates, closes, rets[series_id], ev["date"])
            st["event_day_change_pct"] = pct(st.pop("event_day_change"))
            st["window_cumulative_change_pct"] = pct(
                st.pop("window_cumulative_change"))
            per_series[series_id] = st
        st = event_window_stats(ydates, ylevels,
                                [float("nan") if v is None else v / 100.0
                                 for v in ychg],
                                ev["date"])
        # Recompute US10Y window in bps directly from levels.
        pos = event_position(ydates, ev["date"])
        ystat = {"available": pos is not None}
        if pos is not None:
            start = max(0, pos - 5)
            end = min(len(ydates) - 1, pos + 5)
            ystat.update({
                "event_observation_date": ydates[pos],
                "on_exact_date": ydates[pos] == ev["date"],
                "event_day_change_bps": (round(ychg[pos], 2)
                                         if ydates[pos] == ev["date"] and pos >= 1
                                         else None),
                "event_day_zscore": (trailing_zscore(ychg[pos], ychg[max(0, pos - 60):pos])
                                     if ydates[pos] == ev["date"] and pos >= 1
                                     else None),
                "window_start_date": ydates[start],
                "window_end_date": ydates[end],
                "window_truncated": (pos - 5 < 0) or (pos + 5 > len(ydates) - 1),
                "window_change_bps": round((ylevels[end] - ylevels[start]) * 100.0, 2),
                "yield_level_on_event_date": (ylevels[pos]
                                              if ydates[pos] == ev["date"] else None),
            })
        per_series["us10y"] = ystat
        events_out[ev["id"]] = {
            "date": ev["date"], "label": ev["label"], "kind": ev["kind"],
            "series": per_series,
        }
    results["events"] = events_out

    # --- Rolling volatility (20-day, annualized, percent) ---
    vol_out = {}
    for series_id in ("ihsg", "usdidr"):
        dates, closes = obs[series_id]
        vol = rolling_volatility(rets[series_id])
        vol_map = {d: (None if pd.isna(v) else round(float(v), 3))
                   for d, v in zip(dates, vol)}
        recent = {d: v for d, v in vol_map.items()
                  if "2026-10-01" <= d <= DATA_END and v is not None}
        vol_out[series_id] = {
            "on_2026_11_11": vol_map.get("2026-11-11"),
            "on_2026_11_12": vol_map.get("2026-11-12"),
            "on_2026_11_13": vol_map.get("2026-11-13"),
            "max_oct_nov_2026": max(recent.values()) if recent else None,
            "max_oct_nov_2026_date": (max(recent, key=recent.get)
                                      if recent else None),
            "last_value": vol_map.get(dates[-1]),
            "last_date": dates[-1],
        }
    results["rolling_volatility_20d_pct"] = vol_out

    # --- Global investor decomposition ---
    all_obs = {sid: series_observations(panel, sid) for sid in SERIES_FILES}

    def close_on(series_id, date):
        dates, closes = all_obs[series_id]
        if date in dates:
            return closes[dates.index(date)]
        return None

    def bracket(series_id, d0, d1):
        c0 = close_on(series_id, d0)
        c1 = close_on(series_id, d1)
        if c0 is None or c1 is None:
            return None
        return c1 / c0 - 1.0

    decomp = {}
    # Bracket A: 11 Nov close to 13 Nov close (series with valid data).
    # Bracket B: 11 Nov close to 16 Nov close (first valid USDIDR close
    # after the event; USDIDR closes on 12 and 13 Nov are invalid ticks).
    for name, d1 in (("bracket_11nov_to_13nov", "2026-11-13"),
                     ("bracket_11nov_to_16nov", FIRST_POST_EVENT_VALID_DATE)):
        row = {}
        for series_id in ("ihsg", "eido", "dxy", "usdidr"):
            row[series_id + "_return_pct"] = pct(bracket(series_id, PRE_EVENT_CLOSE_DATE, d1))
        if row["usdidr_return_pct"] is not None and row["dxy_return_pct"] is not None:
            row["usdidr_residual_vs_dxy_pp"] = round(
                row["usdidr_return_pct"] - row["dxy_return_pct"], 4)
        else:
            row["usdidr_residual_vs_dxy_pp"] = None
        if row["ihsg_return_pct"] is not None and row["eido_return_pct"] is not None:
            row["eido_minus_ihsg_pp"] = round(
                row["eido_return_pct"] - row["ihsg_return_pct"], 4)
        row["us10y_change_bps"] = None
        y0 = close_on("us10y", PRE_EVENT_CLOSE_DATE)
        y1 = close_on("us10y", d1)
        if y0 is not None and y1 is not None:
            row["us10y_change_bps"] = round((y1 - y0) * 100.0, 2)
        decomp[name] = row
    # Event-day (12 Nov) single-day moves where computable.
    decomp["event_day_2026_11_12"] = {
        "ihsg_return_pct": pct(iret[idates.index(MAIN_EVENT_DATE)]),
        "eido_return_pct": pct(rets["eido"][obs["eido"][0].index(MAIN_EVENT_DATE)])
        if MAIN_EVENT_DATE in obs["eido"][0] else None,
        "dxy_return_pct": pct(rets["dxy"][obs["dxy"][0].index(MAIN_EVENT_DATE)])
        if MAIN_EVENT_DATE in obs["dxy"][0] else None,
        "usdidr_return_pct": None,
        "usdidr_note": ("Not computable from the downloaded series: the "
                        "Yahoo Finance USD/IDR closes for 12 and 13 Nov 2026 "
                        "fall outside their own daily high-low ranges "
                        "(invalid ticks) and were excluded, never replaced. "
                        "Outlets reported spot prints between about 18,140 "
                        "and 18,250 on 12 Nov (see reported_figures.csv)."),
        "us10y_change_bps": round(ychg[ydates.index(MAIN_EVENT_DATE)], 2)
        if MAIN_EVENT_DATE in ydates else None,
    }
    results["global_investor_decomposition"] = decomp

    # --- Context: 2026 year-to-date moves to the event day ---
    def ytd(series_id, end_date):
        dates, closes = obs[series_id]
        base = None
        for d, c in zip(dates, closes):
            if d <= "2025-12-31":
                base = c
            else:
                break
        end = close_on(series_id, end_date)
        if base is None or end is None:
            return None
        return pct(end / base - 1.0)

    results["context_ytd_to_2026_11_12_pct"] = {
        "ihsg": ytd("ihsg", MAIN_EVENT_DATE),
        "usdidr": None,  # 12 Nov close invalid; use 11 Nov below
        "usdidr_to_2026_11_11": ytd("usdidr", PRE_EVENT_CLOSE_DATE),
        "eido": ytd("eido", MAIN_EVENT_DATE),
        "dxy": ytd("dxy", MAIN_EVENT_DATE),
    }
    results["levels"] = {
        "ihsg_close_2026_11_11": close_on("ihsg", PRE_EVENT_CLOSE_DATE),
        "ihsg_close_2026_11_12": close_on("ihsg", MAIN_EVENT_DATE),
        "ihsg_close_2026_11_13": close_on("ihsg", "2026-11-13"),
        "usdidr_close_2026_11_11": close_on("usdidr", PRE_EVENT_CLOSE_DATE),
        "usdidr_close_2026_11_16": close_on("usdidr", FIRST_POST_EVENT_VALID_DATE),
        "eido_close_2026_11_11": close_on("eido", PRE_EVENT_CLOSE_DATE),
        "eido_close_2026_11_12": close_on("eido", MAIN_EVENT_DATE),
        "dxy_close_2026_11_11": close_on("dxy", PRE_EVENT_CLOSE_DATE),
        "dxy_close_2026_11_12": close_on("dxy", MAIN_EVENT_DATE),
        "us10y_yield_2026_11_11": close_on("us10y", PRE_EVENT_CLOSE_DATE),
        "us10y_yield_2026_11_12": close_on("us10y", MAIN_EVENT_DATE),
    }
    return results, obs, rets, (ydates, ylevels, ychg)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_charts(panel, obs, rets, ylevels_pack):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(CHART_DIR, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                         "axes.grid": True, "grid.alpha": 0.3})
    event_lines = [
        ("2026-09-30", "30 Sep 2026\nHoax fact-check", "grey"),
        ("2026-10-30", "30 Oct 2026\nMA decision", "darkorange"),
        ("2026-11-11", "11 Nov 2026\nHMP proposal", "purple"),
        ("2026-11-12", "12 Nov 2026\nVP resigns", "red"),
        ("2026-11-13", "13 Nov 2026\nMPR meeting", "brown"),
    ]

    import matplotlib.dates as mdates
    import matplotlib.transforms as mtransforms

    def add_events(ax):
        # Stagger labels at different heights so the clustered
        # Oct 30 to Nov 13 markers stay readable.
        heights = [0.97, 0.80, 0.63, 0.46, 0.29]
        blend = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
        for (d, label, color), h in zip(event_lines, heights):
            ax.axvline(pd.Timestamp(d), color=color, lw=1, ls="--", alpha=0.8)
            ax.text(mdates.date2num(pd.Timestamp(d)) + 2, h, label,
                    transform=blend, fontsize=7, color=color, va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec=color, alpha=0.85))

    # 1. IHSG timeline
    dates, closes = obs["ihsg"]
    x = pd.to_datetime(dates)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(x, closes, color="#1f4e79", lw=1.2)
    ax.set_title("IHSG daily close, Oct 2025 to Nov 2026, with event markers")
    ax.set_ylabel("Index level")
    add_events(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "ihsg_timeline.png"))
    plt.close(fig)

    # 2. USD/IDR timeline with invalid ticks flagged
    raw = load_raw("usdidr")
    rx = pd.to_datetime(raw["date"])
    fig, ax = plt.subplots(figsize=(10, 4.2))
    valid = raw[raw["close_valid"]]
    ax.plot(pd.to_datetime(valid["date"]), valid["close"],
            color="#7a1f1f", lw=1.1, label="Valid daily close")
    invalid = raw[~raw["close_valid"]]
    ax.scatter(pd.to_datetime(invalid["date"]), invalid["close"],
               color="red", marker="x", s=42,
               label="Invalid close (outside daily range, excluded)")
    ax.set_title("USD/IDR daily close with data-quality flags")
    ax.set_ylabel("IDR per USD")
    add_events(ax)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "usdidr_timeline.png"))
    plt.close(fig)

    # 3. Cumulative returns since the 11 Nov 2026 close (pre-event anchor)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    anchor = PRE_EVENT_CLOSE_DATE
    for series_id, color, label in (
            ("ihsg", "#1f4e79", "IHSG"),
            ("eido", "#2e7d32", "EIDO (global investor proxy)"),
            ("dxy", "#616161", "DXY (US dollar index)"),
            ("usdidr", "#7a1f1f", "USD/IDR (valid closes only)")):
        dts, cls = obs[series_id]
        if anchor not in dts:
            continue
        i0 = dts.index(anchor)
        xs = [pd.Timestamp(anchor)]
        ys = [0.0]
        for i in range(i0 + 1, len(dts)):
            if dts[i] > "2026-11-17":
                break
            xs.append(pd.Timestamp(dts[i]))
            ys.append((cls[i] / cls[i0] - 1.0) * 100.0)
        style = "--" if series_id == "usdidr" else "-"
        ax.plot(xs, ys, marker="o", ms=3, lw=1.2, color=color, label=label,
                linestyle=style)
    ax.axhline(0, color="black", lw=0.7)
    ax.axvline(pd.Timestamp(MAIN_EVENT_DATE), color="red", lw=1, ls="--")
    ax.set_title("Cumulative return since the 11 Nov 2026 close "
                 "(last close before the resignation)")
    ax.set_ylabel("Cumulative return (%)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "event_window_comparison.png"))
    plt.close(fig)

    # 4. Rolling volatility
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for series_id, color, label in (("ihsg", "#1f4e79", "IHSG"),
                                    ("usdidr", "#7a1f1f", "USD/IDR")):
        dts, cls = obs[series_id]
        vol = rolling_volatility(rets[series_id])
        ax.plot(pd.to_datetime(dts), vol, color=color, lw=1.1, label=label)
    ax.set_title("Rolling 20-day volatility of daily returns (annualized, %)")
    ax.set_ylabel("Volatility (%)")
    add_events(ax)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "rolling_volatility.png"))
    plt.close(fig)


# ---------------------------------------------------------------------------

def main():
    panel, quality = build_panel()
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    out = panel.copy()
    out["usdidr_close_valid"] = out["usdidr_close_valid"].map(
        lambda v: "" if pd.isna(v) else str(bool(v)))
    out.to_csv(PROCESSED_PATH, index=False)
    results, obs, rets, ypack = analyze(panel)
    results["data_quality"] = quality
    results["method_notes"] = [
        "Returns are simple close-to-close returns on each series' own "
        "observation calendar; gaps are never filled.",
        "A close outside its own daily high-low range is treated as an "
        "invalid tick, excluded from all calculations, and never replaced.",
        "US 10Y (^TNX) is analysed as yield level changes in basis points, "
        "not percentage returns.",
        "Event windows are [-5, +5] observations around the event "
        "observation; windows are truncated at the data end (17 Nov 2026) "
        "and the actual dates used are reported.",
    ]
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    make_charts(panel, obs, rets, ypack)
    print("Panel rows:", len(panel))
    print("Cross-check:", json.dumps(results["crosscheck_ihsg_2026_11_12"], indent=2))
    print("Decomposition:", json.dumps(results["global_investor_decomposition"], indent=2))
    print("Wrote", RESULTS_PATH)


if __name__ == "__main__":
    sys.exit(main())
