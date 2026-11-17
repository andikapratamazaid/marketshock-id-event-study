# Data Sources

Retrieval date for all downloaded series: **17 November 2026**.
All downloads were performed by `analysis/fetch_data.py` using only the
Python standard library. Raw files are stored exactly as downloaded in
`data/raw/`; no raw value has been edited.

## Downloaded series (all five fetched successfully)

| Series | File | Source used | URL pattern | Rows | Date range |
|---|---|---|---|---|---|
| IHSG (Jakarta Composite Index) | `data/raw/ihsg.csv` | Yahoo Finance chart API | `https://query1.finance.yahoo.com/v8/finance/chart/%5EJKSE?period1=1759276800&period2=1795046400&interval=1d&events=history` | 273 | 2025-10-01 to 2026-11-17 |
| USD/IDR | `data/raw/usdidr.csv` | Yahoo Finance chart API | `https://query1.finance.yahoo.com/v8/finance/chart/IDR%3DX?period1=1759276800&period2=1795046400&interval=1d&events=history` | 293 | 2025-09-30 to 2026-11-17 |
| iShares MSCI Indonesia ETF (EIDO) | `data/raw/eido.csv` | Yahoo Finance chart API | `https://query1.finance.yahoo.com/v8/finance/chart/EIDO?period1=1759276800&period2=1795046400&interval=1d&events=history` | 284 | 2025-10-01 to 2026-11-16 |
| US Dollar Index (DXY) | `data/raw/dxy.csv` | Yahoo Finance chart API | `https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?period1=1759276800&period2=1795046400&interval=1d&events=history` | 285 | 2025-10-01 to 2026-11-17 |
| US 10-year Treasury yield (^TNX) | `data/raw/us10y.csv` | Yahoo Finance chart API | `https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?period1=1759276800&period2=1795046400&interval=1d&events=history` | 284 | 2025-10-01 to 2026-11-16 |

Notes:

- The ^TNX values are yield levels in percent (for example 5.103 means
  5.103 percent). The analysis treats this series as yield changes in
  basis points, not percentage returns.
- The USD/IDR raw file contains one row dated 2025-09-30 (a timezone
  artifact of the source feed) and rows for some weekend dates; each
  series is analysed on its own observation calendar.
- The final observations (16 and 17 November 2026) may still have been
  partial-day prints at retrieval time. Event windows that extend past
  13 November 2026 are labelled as truncated in the results.

## Fallback source status

The fallback source, Stooq daily CSV (`https://stooq.com/q/d/l/?s=<symbol>&i=d`),
was attempted for USD/IDR on 17 November 2026 but was **not reachable from
this environment** (the server closed the connection without a response).
Because all five series were obtained from the primary source, the
fallback was not needed for any other series. No series in this project
is missing.

## Data-quality disclosure: USD/IDR invalid closes

The Yahoo Finance USD/IDR feed (both `IDR=X` and `USDIDR=X` return the
same feed) contains corrupted close values on 27 of its 293 rows: the
printed close falls **outside the same row's own high-low range**, which
is impossible for a genuine daily close. Examples in the event period:

- 2026-11-12: close 17,489.5 against a daily range of 18,140.0 to 18,260.6
- 2026-11-13: close 17,633.1 against a daily range of 18,185.0 to 18,254.4

Treatment applied in `analysis/run_analysis.py` (documented, mechanical,
and fully reproducible):

1. A close is valid only if it lies inside its own daily high-low range.
2. Invalid closes are treated as **missing**. They are excluded from
   every return, window, and volatility calculation.
3. Invalid closes are **never replaced, interpolated, or forward-filled**.
   The processed panel (`data/processed/market_daily.csv`) leaves those
   cells empty and flags them in the `usdidr_close_valid` column.
4. Consequences, stated openly: the USD/IDR close-to-close return for
   12 November 2026 **cannot be computed** from the downloaded series.
   The decomposition therefore brackets the event with the nearest valid
   closes (11 November and 16 November 2026), and the event-day spot
   level is documented from named news outlets in
   `data/reported_figures.csv` instead.

No other series had any invalid closes (0 of 273 IHSG rows, 0 of 284
EIDO rows, 0 of 285 DXY rows, 0 of 284 US 10Y rows).

## Reported figures (not downloaded)

Figures that are not available as a downloadable daily series (daily
foreign investor net buy/sell on the IDX, the SBN 10-year yield on
12 November 2026, the MSCI announcement) are stored separately in
`data/reported_figures.csv` with the publishing outlet named for each
value. They are used only as reported evidence, never merged into the
downloaded price panel.
