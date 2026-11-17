#!/usr/bin/env python3
"""Build dashboard/marketshock_dashboard.html from the analysis results.

Reads output/analysis_results.json and the PNG charts in charts/, and
writes ONE self-contained HTML file (charts embedded as base64). Run
after analysis/run_analysis.py.
"""

import base64
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(PROJECT_ROOT, "output", "analysis_results.json")
CHART_DIR = os.path.join(PROJECT_ROOT, "charts")
OUT = os.path.join(PROJECT_ROOT, "dashboard", "marketshock_dashboard.html")


def img_tag(filename, alt):
    path = os.path.join(CHART_DIR, filename)
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return ('<img src="data:image/png;base64,' + b64 + '" alt="' + alt
            + '" style="max-width:100%;height:auto;">')


def fmt_pct(v, digits=2):
    if v is None:
        return "n/a"
    return ("+" if v > 0 else "") + f"{v:.{digits}f}%"


def fmt_bps(v):
    if v is None:
        return "n/a"
    return ("+" if v > 0 else "") + f"{v:.1f} bps"


def main():
    with open(RESULTS) as fh:
        r = json.load(fh)
    cc = r["crosscheck_ihsg_2026_11_12"]
    dec = r["global_investor_decomposition"]
    day = dec["event_day_2026_11_12"]
    bA = dec["bracket_11nov_to_13nov"]
    bB = dec["bracket_11nov_to_16nov"]
    vol = r["rolling_volatility_20d_pct"]["ihsg"]
    ytd = r["context_ytd_to_2026_11_12_pct"]
    lv = r["levels"]

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MarketShock ID: Market Reaction to the Vice Presidential Resignation</title>
<style>
  body { font-family: "Segoe UI", Arial, sans-serif; margin: 0; background: #f2f4f7; color: #1c2733; }
  header { background: #16324f; color: #fff; padding: 22px 28px; }
  header h1 { margin: 0 0 6px; font-size: 22px; }
  header p { margin: 0; opacity: .88; font-size: 13.5px; max-width: 900px; }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 20px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 18px; }
  .card { background: #fff; border: 1px solid #d5dce4; border-radius: 8px; padding: 14px; }
  .card .k { font-size: 12px; color: #5a6b7d; text-transform: uppercase; letter-spacing: .04em; }
  .card .v { font-size: 24px; font-weight: 700; margin: 4px 0 2px; }
  .card .s { font-size: 12px; color: #5a6b7d; }
  section { background: #fff; border: 1px solid #d5dce4; border-radius: 8px; padding: 18px; margin-bottom: 18px; }
  h2 { margin: 0 0 10px; font-size: 17px; color: #16324f; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { border: 1px solid #d5dce4; padding: 6px 8px; text-align: left; }
  th { background: #eef2f6; }
  .warn { background: #fdf3e3; border: 1px solid #e8cf9e; border-radius: 8px; padding: 12px 14px; font-size: 13px; margin-bottom: 18px; }
  .small { font-size: 12.5px; color: #44566a; }
  footer { font-size: 12px; color: #5a6b7d; padding: 0 4px 26px; }
</style>
</head>
<body>
<header>
  <h1>MarketShock ID: Indonesia Market Reaction to the Vice Presidential Resignation</h1>
  <p>An event study with a global investor lens. Daily market data downloaded on
  17 November 2026 (Yahoo Finance). Research question: did global investors read the
  12 November 2026 resignation of Vice President Gibran Rakabuming Raka as risk relief
  or as added uncertainty?</p>
</header>
<div class="wrap">

  <div class="warn"><strong>Attribution warning.</strong> MSCI announced its index review
  results on the same day as the resignation, 12 November 2026 (BRPT and BRMS removed from
  the Global Standard Index, effective 1 December 2026). No part of that day's market move
  can be attributed to the resignation alone. Figures below describe market behaviour
  around the events; they do not claim single-cause attribution.</div>

  <div class="cards">
    <div class="card"><div class="k">IHSG, 12 Nov 2026</div><div class="v">__IHSG_DAY__</div>
      <div class="s">Close __IHSG_CLOSE__ (reported: 5,250.90, +2.66%)</div></div>
    <div class="card"><div class="k">EIDO (global proxy), 12 Nov</div><div class="v">__EIDO_DAY__</div>
      <div class="s">Global investors moved with the local index</div></div>
    <div class="card"><div class="k">USD/IDR, 11 to 16 Nov bracket</div><div class="v">__IDR_BRACKET__</div>
      <div class="s">Event-day closes are invalid ticks in the source feed; see data notes</div></div>
    <div class="card"><div class="k">IDR residual vs DXY</div><div class="v">__RESIDUAL__</div>
      <div class="s">Indonesia-specific FX premium over the bracket: none measured</div></div>
    <div class="card"><div class="k">US 10Y yield, 12 Nov</div><div class="v">__US10Y_DAY__</div>
      <div class="s">Global rates headwind on the day, to __US10Y_LEVEL__%</div></div>
    <div class="card"><div class="k">Foreign flow, 12 Nov (reported)</div><div class="v">Net buy Rp443.53 B</div>
      <div class="s">Against about Rp127 T net selling year-to-date (Kontan)</div></div>
    <div class="card"><div class="k">IHSG year-to-date to 12 Nov</div><div class="v">__IHSG_YTD__</div>
      <div class="s">The event landed on an already stressed market</div></div>
    <div class="card"><div class="k">IHSG 20-day volatility, 12 Nov</div><div class="v">__VOL__%</div>
      <div class="s">Annualised; the October to November maximum</div></div>
  </div>

  <section>
    <h2>Event timeline</h2>
    <table>
      <tr><th>Date</th><th>Event</th><th>Market note</th></tr>
      <tr><td>May 2026</td><td>Hoax wave: recycled 2024 Solo mayor resignation video claims the VP resigned</td><td>Documented as background; no single verified timestamp to window</td></tr>
      <tr><td>30 Sep 2026</td><td>Kompas.com fact check debunks the revived resignation claim</td><td>IHSG -0.83% on the day (z -0.86); no discrete market signature</td></tr>
      <tr><td>30 Oct 2026</td><td>Supreme Court cassation No. 742 K/TUN/2026 annuls the education equivalency letter</td><td>IHSG -0.80% on the day; -7.15% cumulative across the 23 Oct to 6 Nov window</td></tr>
      <tr><td>11 Nov 2026</td><td>120 DPR members from 8 factions propose Hak Menyatakan Pendapat; ministry revokes the letter</td><td>IHSG -0.21%; rupiah weaker mainly with a strong global dollar (DXY +0.67%)</td></tr>
      <tr><td>12 Nov 2026</td><td><strong>VP Gibran submits his resignation to the MPR and the President</strong></td><td>IHSG +2.66%, EIDO +2.55%, reported foreign net buy; reported SBN 10Y yield up to 7.63%. MSCI review announced the same day</td></tr>
      <tr><td>13 Nov 2026</td><td>MPR leadership meets; 60-day vacancy process under Article 8(2) of the 1945 Constitution</td><td>IHSG +1.78% further, to 5,344.41</td></tr>
    </table>
  </section>

  <section>
    <h2>IHSG with event markers</h2>
    __IMG_IHSG__
  </section>

  <section>
    <h2>Cumulative returns since the 11 November 2026 close</h2>
    __IMG_WINDOW__
    <p class="small">USD/IDR is drawn dashed through its valid closes only. Its 12 and
    13 November closes in the source feed fall outside their own daily ranges (invalid
    ticks) and were excluded, never replaced.</p>
  </section>

  <section>
    <h2>Global investor decomposition</h2>
    <table>
      <tr><th>Measure</th><th>11 to 13 Nov 2026</th><th>11 to 16 Nov 2026</th></tr>
      <tr><td>IHSG cumulative return</td><td>__BA_IHSG__</td><td>__BB_IHSG__</td></tr>
      <tr><td>EIDO cumulative return</td><td>__BA_EIDO__</td><td>__BB_EIDO__</td></tr>
      <tr><td>EIDO minus IHSG</td><td>__BA_GAP__</td><td>__BB_GAP__</td></tr>
      <tr><td>DXY cumulative return</td><td>__BA_DXY__</td><td>__BB_DXY__</td></tr>
      <tr><td>USD/IDR cumulative change</td><td>n/a (invalid closes)</td><td>__BB_IDR__</td></tr>
      <tr><td>USD/IDR residual vs DXY</td><td>n/a</td><td>__BB_RESID__</td></tr>
      <tr><td>US 10Y yield change</td><td>__BA_US10Y__</td><td>__BB_US10Y__</td></tr>
    </table>
    <p class="small">Reading: global investors (EIDO) matched the local relief move on the
    day (+2.55% vs +2.66%) and lagged only modestly over the following days, part of which
    is currency translation in a dollar-denominated fund. Over the 11 to 16 November
    bracket the rupiah weakened slightly less than the broad dollar move, so the
    downloaded data show no added Indonesia-specific currency premium across that span.
    Reported spot prints on 12 November itself (about 18,140 to 18,250) and the reported
    rise in the SBN 10-year yield to 7.63% point to more caution in currency and rates
    than in equities.</p>
  </section>

  <section>
    <h2>USD/IDR with data-quality flags</h2>
    __IMG_IDR__
  </section>

  <section>
    <h2>Rolling volatility</h2>
    __IMG_VOL__
    <p class="small">IHSG volatility was already extreme before the event (53.3%
    annualised on 11 November) because of the late-October selloff, and peaked at 54.5%
    on 12 November. USD/IDR volatility readings that would span the invalid closes are
    not computable and are left blank by construction.</p>
  </section>

  <section>
    <h2>Conclusion, bounded by the data</h2>
    <p>No panic, and a measurable relief reaction in equities shared by local and global
    investors: IHSG +2.66% and EIDO +2.55% on 12 November with reported foreign net
    buying of Rp443.53 billion. Currency and rates evidence, which rests partly on
    reporting, shows more caution. The structural backdrop remains a market down
    __IHSG_YTD2__ year-to-date and about Rp127 trillion of reported foreign net selling
    in 2026, which one calm week does not reverse. Because of the same-day MSCI
    announcement, none of the rally can be credited to the resignation alone. Full
    method, limitations, and sources: see the project README and findings report.</p>
  </section>

  <footer>MarketShock ID event study. Data: Yahoo Finance daily series retrieved
  17 November 2026; reported figures from named Indonesian outlets (Kontan, CNBC
  Indonesia, Bareksa, Suara.com). This dashboard is a data analysis artefact, not
  investment advice.</footer>
</div>
</body>
</html>
"""

    def pp(v):
        return "n/a" if v is None else f"{v:+.2f} pp"

    repl = {
        "__IHSG_DAY__": fmt_pct(day["ihsg_return_pct"]),
        "__IHSG_CLOSE__": f"{cc['fetched_close']:,.2f}",
        "__EIDO_DAY__": fmt_pct(day["eido_return_pct"]),
        "__IDR_BRACKET__": fmt_pct(bB["usdidr_return_pct"]),
        "__RESIDUAL__": pp(bB["usdidr_residual_vs_dxy_pp"]),
        "__US10Y_DAY__": fmt_bps(day["us10y_change_bps"]),
        "__US10Y_LEVEL__": f"{lv['us10y_yield_2026_11_12']:.3f}",
        "__IHSG_YTD__": fmt_pct(ytd["ihsg"]),
        "__IHSG_YTD2__": fmt_pct(ytd["ihsg"]),
        "__VOL__": f"{vol['on_2026_11_12']:.1f}",
        "__BA_IHSG__": fmt_pct(bA["ihsg_return_pct"]),
        "__BB_IHSG__": fmt_pct(bB["ihsg_return_pct"]),
        "__BA_EIDO__": fmt_pct(bA["eido_return_pct"]),
        "__BB_EIDO__": fmt_pct(bB["eido_return_pct"]),
        "__BA_GAP__": pp(bA["eido_minus_ihsg_pp"]),
        "__BB_GAP__": pp(bB["eido_minus_ihsg_pp"]),
        "__BA_DXY__": fmt_pct(bA["dxy_return_pct"]),
        "__BB_DXY__": fmt_pct(bB["dxy_return_pct"]),
        "__BB_IDR__": fmt_pct(bB["usdidr_return_pct"]),
        "__BB_RESID__": pp(bB["usdidr_residual_vs_dxy_pp"]),
        "__BA_US10Y__": fmt_bps(bA["us10y_change_bps"]),
        "__BB_US10Y__": fmt_bps(bB["us10y_change_bps"]),
        "__IMG_IHSG__": img_tag("ihsg_timeline.png", "IHSG timeline with event markers"),
        "__IMG_WINDOW__": img_tag("event_window_comparison.png", "Cumulative returns since 11 Nov 2026"),
        "__IMG_IDR__": img_tag("usdidr_timeline.png", "USD/IDR with data quality flags"),
        "__IMG_VOL__": img_tag("rolling_volatility.png", "Rolling 20-day volatility"),
    }
    for key, value in repl.items():
        html = html.replace(key, value)
    with open(OUT, "w") as fh:
        fh.write(html)
    print("Wrote", OUT, len(html), "bytes")


if __name__ == "__main__":
    main()
