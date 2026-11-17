#!/usr/bin/env python3
"""Fetch daily market series for the MarketShock ID event study.

Primary source: Yahoo Finance chart API (query1.finance.yahoo.com).
Fallback source: Stooq daily CSV download.
Standard library only (urllib). No data is invented: a series that
cannot be fetched from either source is reported as FAILED and must
be documented as missing in data/data_sources.md.

Output: data/raw/<series_id>.csv with columns
    date,open,high,low,close,volume
and a fetch manifest at output/fetch_manifest.json.
"""

import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
OUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Coverage window: 1 Oct 2025 to 18 Nov 2026 (period2 is exclusive).
PERIOD1 = int(datetime(2025, 10, 1, tzinfo=timezone.utc).timestamp())
PERIOD2 = int(datetime(2026, 11, 19, tzinfo=timezone.utc).timestamp())

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
             "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"

SERIES = [
    {
        "id": "ihsg",
        "label": "IHSG (Jakarta Composite Index)",
        "yahoo": "^JKSE",
        "stooq": "^jkse",
    },
    {
        "id": "usdidr",
        "label": "USD/IDR exchange rate",
        "yahoo": "IDR=X",
        "stooq": "usdidr",
    },
    {
        "id": "eido",
        "label": "iShares MSCI Indonesia ETF (EIDO)",
        "yahoo": "EIDO",
        "stooq": "eido.us",
    },
    {
        "id": "dxy",
        "label": "US Dollar Index (DXY)",
        "yahoo": "DX-Y.NYB",
        "stooq": "^dxy",
    },
    {
        "id": "us10y",
        "label": "US 10-year Treasury yield (CBOE ^TNX)",
        "yahoo": "^TNX",
        "stooq": "10usy.b",
    },
]


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_yahoo(symbol):
    """Return list of dict rows from the Yahoo Finance chart API."""
    encoded = urllib.parse.quote(symbol, safe="")
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + encoded
        + "?period1=" + str(PERIOD1)
        + "&period2=" + str(PERIOD2)
        + "&interval=1d&events=history"
    )
    payload = json.loads(http_get(url).decode("utf-8"))
    result = payload["chart"]["result"]
    if not result:
        raise ValueError("empty chart result")
    result = result[0]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, ts in enumerate(timestamps):
        close = quote["close"][i]
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append({
            "date": day,
            "open": quote["open"][i],
            "high": quote["high"][i],
            "low": quote["low"][i],
            "close": close,
            "volume": quote.get("volume", [None] * len(timestamps))[i],
        })
    if not rows:
        raise ValueError("no usable rows")
    return rows, url


def fetch_stooq(symbol):
    """Return list of dict rows from a Stooq daily CSV download."""
    url = "https://stooq.com/q/d/l/?s=" + urllib.parse.quote(symbol, safe="") + "&i=d"
    text = http_get(url).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for r in reader:
        try:
            day = r["Date"].strip()
            dt = datetime.strptime(day, "%Y-%m-%d")
        except Exception:
            continue
        if dt < datetime(2025, 10, 1) or dt > datetime(2026, 11, 18):
            continue
        def num(key):
            try:
                return float(r[key])
            except Exception:
                return None
        close = num("Close")
        if close is None:
            continue
        rows.append({
            "date": day,
            "open": num("Open"),
            "high": num("High"),
            "low": num("Low"),
            "close": close,
            "volume": num("Volume"),
        })
    if not rows:
        raise ValueError("no usable rows")
    rows.sort(key=lambda x: x["date"])
    return rows, url


def fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(round(value, 6))
    return str(value)


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = []
    for spec in SERIES:
        entry = {"id": spec["id"], "label": spec["label"]}
        rows = None
        used_url = None
        used_source = None
        errors = []
        for name, fn, sym in (
            ("Yahoo Finance chart API", fetch_yahoo, spec["yahoo"]),
            ("Stooq daily CSV", fetch_stooq, spec["stooq"]),
        ):
            try:
                rows, used_url = fn(sym)
                used_source = name
                break
            except Exception as exc:  # noqa: BLE001 - record and try next source
                errors.append(name + ": " + repr(exc))
                rows = None
        if rows is None:
            entry.update({
                "status": "FAILED",
                "errors": errors,
            })
            print("FAILED  " + spec["id"] + " -> " + " | ".join(errors))
            manifest.append(entry)
            continue
        path = os.path.join(RAW_DIR, spec["id"] + ".csv")
        with open(path, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["date", "open", "high", "low", "close", "volume"])
            for r in rows:
                writer.writerow([r["date"], fmt(r["open"]), fmt(r["high"]),
                                 fmt(r["low"]), fmt(r["close"]), fmt(r["volume"])])
        entry.update({
            "status": "OK",
            "source": used_source,
            "url_pattern": used_url,
            "rows": len(rows),
            "date_min": rows[0]["date"],
            "date_max": rows[-1]["date"],
            "errors": errors,
        })
        print("OK      " + spec["id"] + " via " + used_source
              + " rows=" + str(len(rows))
              + " " + rows[0]["date"] + ".." + rows[-1]["date"])
        manifest.append(entry)
        time.sleep(1)
    with open(os.path.join(OUT_DIR, "fetch_manifest.json"), "w") as fh:
        json.dump({"retrieval_date": "2026-11-17", "series": manifest}, fh, indent=2)
    ok = sum(1 for m in manifest if m["status"] == "OK")
    print("Fetched " + str(ok) + "/" + str(len(manifest)) + " series.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
