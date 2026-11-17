# MarketShock ID

## Event Study: Indonesia Market Reaction to the Vice Presidential Resignation, with a Global Investor Lens

On Thursday, 12 November 2026, Gibran Rakabuming Raka submitted his
resignation as Vice President of Indonesia to the MPR and to President
Prabowo Subianto, after the Supreme Court annulled the education
equivalency letter used in his 2024 candidacy (cassation decision
No. 742 K/TUN/2026, 30 October 2026) and 120 DPR members proposed the
Hak Menyatakan Pendapat process on 11 November 2026. The claim that he
had resigned had already circulated twice as a hoax, in May 2026 and
again in September to October 2026.

This project measures how financial markets behaved around those events
using real, downloaded daily market data, and asks one question:

**Did global investors read the resignation as political risk relief, or
as added uncertainty for Indonesia?**

The short answer, bounded by the data: equities, local and global,
reacted with measurable relief and reported foreign flow was net buying
on the day, while currency and rates evidence shows more caution, and
the same-day MSCI index announcement makes single-cause attribution
impossible. The full reasoning is in `docs/findings_report.md`.

## Key results (computed from the downloaded data)

| Measure | Result |
|---|---|
| IHSG on 12 Nov 2026 | **+2.66%**, close 5,250.90 (fetched series matches the reported close and gain to the decimal) |
| EIDO (iShares MSCI Indonesia ETF) on 12 Nov 2026 | **+2.55%**, nearly identical to the local index |
| IHSG cumulative, 11 to 13 Nov 2026 | +4.48% |
| EIDO cumulative, 11 to 16 Nov 2026 | +2.94% against IHSG +4.03% (gap partly currency translation) |
| USD/IDR, 11 to 16 Nov 2026 bracket | +0.45% against DXY +0.62%; Indonesia-specific residual **-0.17 pp** |
| US 10-year yield on 12 Nov 2026 | +10.5 bps to 5.103% (global rates headwind) |
| IHSG window around the MA decision (23 Oct to 6 Nov) | **-7.15%**, the largest sustained repricing of the study period |
| IHSG year-to-date to 12 Nov 2026 | -39.27% (the event landed on an already stressed market) |
| Foreign flow on 12 Nov 2026 (reported, Kontan) | Net buy Rp443.53 billion, against about Rp127 trillion net selling year-to-date |
| SBN 10-year yield on 12 Nov 2026 (reported) | 7.63%, up about 7.9 bps |

## Data

All price data are real public data downloaded on **17 November 2026**
with `analysis/fetch_data.py` (Python standard library only). No data
were fabricated, and gaps were never filled.

| Series | Source | Rows | Range |
|---|---|---|---|
| IHSG (^JKSE) | Yahoo Finance chart API | 273 | 1 Oct 2025 to 17 Nov 2026 |
| USD/IDR (IDR=X) | Yahoo Finance chart API | 293 | 30 Sep 2025 to 17 Nov 2026 |
| EIDO | Yahoo Finance chart API | 284 | 1 Oct 2025 to 16 Nov 2026 |
| DXY (DX-Y.NYB) | Yahoo Finance chart API | 285 | 1 Oct 2025 to 17 Nov 2026 |
| US 10Y yield (^TNX) | Yahoo Finance chart API | 284 | 1 Oct 2025 to 16 Nov 2026 |

The Stooq fallback was attempted but was not reachable from the build
environment; it was not needed because the primary source delivered all
five series. Full provenance, including exact URL patterns, is in
`data/data_sources.md`.

**Data-quality disclosure.** The Yahoo Finance USD/IDR feed contains 27
corrupted closes (the close falls outside the same day's high-low
range), including 12 and 13 November 2026. Those closes are treated as
missing, excluded from every calculation, and never replaced. The
event-day rupiah return is therefore not computed from the downloaded
series; the analysis brackets the event with the nearest valid closes
(11 and 16 November) and documents the event-day spot level from named
news outlets in `data/reported_figures.csv`. One test in the suite
exists solely to prove those cells stayed empty.

## Methodology

- Simple close-to-close daily returns on each series' own observation
  calendar.
- Event windows of [-5, +5] observations around 30 October, 11 November,
  and 12 November 2026, with event-day moves scaled by trailing 60-day
  volatility (z-scores). The 30 September 2026 Kompas.com fact-check is
  used as the observable marker for the hoax wave.
- Rolling 20-day volatility (annualised) for IHSG and USD/IDR.
- Global investor decomposition: EIDO against IHSG (global versus local
  pricing), USD/IDR against DXY (the residual is the Indonesia-specific
  currency move), and the US 10-year yield as the global risk backdrop.
- The US 10-year series is analysed as yield changes in basis points.

## Limitations (summary)

1. MSCI announced its index review on the same day as the resignation
   (BRPT and BRMS removed from the Global Standard Index, effective
   1 December 2026). Single-cause attribution is impossible.
2. The IHSG had fallen 39.27% year-to-date into the event; a technical
   rebound cannot be separated from relief.
3. The USD/IDR event-day closes are invalid ticks in the source feed
   (see the disclosure above).
4. The post-event window ends 17 November 2026, three trading days
   after the event. The 60-day succession process is still open.
5. EIDO is dollar denominated and trades in US hours; it is an
   imperfect proxy for global investor sentiment.
6. Indonesian bond yield and foreign-flow evidence comes from named
   outlet reporting, not downloadable series.
7. Full limitation list: `docs/findings_report.md`, Section 7.

## Project structure

```
marketshock-id-event-study/
  README.md
  analysis/
    fetch_data.py            Download the five series (stdlib only)
    run_analysis.py          Panel, event study, decomposition, charts
  dashboard/
    build_dashboard.py       Builds the self-contained HTML dashboard
    marketshock_dashboard.html
  data/
    data_sources.md          Provenance and data-quality disclosure
    events_timeline.csv      Event markers used in the study
    reported_figures.csv     Reported (not downloaded) figures, sourced
    raw/                     The five series exactly as downloaded
    processed/market_daily.csv
  docs/
    events_timeline.md       Readable event timeline
    findings_report.md       Full findings report
  charts/                    Four PNG charts
  output/
    analysis_results.json    Every computed figure used in the reports
    fetch_manifest.json
  tests/
    test_marketshock.py      25 tests: math, window logic, panel integrity
```

## How to reproduce

```bash
python3 analysis/fetch_data.py     # downloads data/raw/*.csv
python3 analysis/run_analysis.py   # panel, results JSON, charts
python3 dashboard/build_dashboard.py
python3 -m unittest discover -s tests -v
```

Requires Python 3 with pandas and matplotlib for the analysis step
(the fetch step itself is standard library only). Open
`dashboard/marketshock_dashboard.html` in any browser for the summary
view; it is a single self-contained file.

## A note on tone

This is a market data study. It reports what prices and reported flows
did around a political event, separates global from domestic price
pressure where the data allow it, and states plainly where they do not.
It takes no position on the underlying legal case or on any political
actor.
