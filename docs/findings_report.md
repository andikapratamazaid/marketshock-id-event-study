# Findings Report

## MarketShock ID: Indonesia Market Reaction to the Vice Presidential Resignation, with a Global Investor Lens

Event study based on downloaded daily market data retrieved on 17 November
2026. All computed figures come from `output/analysis_results.json`, produced
by `analysis/run_analysis.py` from the raw series in `data/raw/`. Figures that
could not be downloaded are labelled as reported figures and are listed with
their sources in `data/reported_figures.csv`.

## 1. Research question

When Vice President Gibran Rakabuming Raka resigned on 12 November 2026, did
global investors read the event as political risk relief or as added
uncertainty for Indonesia? The study answers with market prices: the local
equity index (IHSG), the instrument global investors actually trade (the
iShares MSCI Indonesia ETF, EIDO, listed in the United States), the rupiah
(USD/IDR), and the global backdrop (US Dollar Index and the US 10-year
Treasury yield).

## 2. Method in brief

- Daily closes from 1 October 2025 to 17 November 2026 for IHSG, USD/IDR,
  EIDO, DXY, and the US 10-year yield, all from the Yahoo Finance chart API
  (see `data/data_sources.md`).
- Simple close-to-close daily returns on each series' own observation
  calendar. Gaps are never filled.
- Event windows of 5 observations before to 5 after each event date, plus
  the event-day move measured against trailing 60-day volatility (a simple
  z-score). Post-event windows are truncated at the data end,
  17 November 2026, and the actual dates used are always reported.
- The US 10-year yield is analysed as level changes in basis points.
- Data-quality rule: a close outside its own daily high-low range is an
  invalid tick. It is excluded and never replaced. This rule removes the
  Yahoo Finance USD/IDR closes of 12 and 13 November 2026, so the event-day
  rupiah return is not computable from the downloaded series and is handled
  through bracketing closes and reported spot prints (Section 5).
- Cross-check: the downloaded IHSG close for 12 November 2026 is 5,250.90
  with a daily return of +2.66 percent, matching the reported close of
  5,250.90 and the reported gain of 2.66 percent to the decimal. The
  downloaded series is therefore consistent with exchange reporting for
  the main event day.

## 3. Context: the market was already stressed

The resignation did not land on a calm market. From the last close of 2025
to 12 November 2026, the IHSG fell 39.27 percent and EIDO fell 44.01
percent, while the rupiah depreciated 8.56 percent against the US dollar
(to the 11 November close) and the dollar index rose 4.98 percent. The
steepest sustained decline of the whole study period sits in the window
around the Supreme Court decision (Section 4.2). Twenty-day IHSG
volatility was already 53.3 percent annualised on 11 November 2026, an
extremely stressed reading, before the resignation happened. Every
event-day z-score in this report is therefore measured against an already
turbulent baseline, which mechanically makes the scores look smaller than
they would in a calm period.

## 4. Findings by event window

### 4.1 Hoax wave marker, 30 September 2026 (fact-check publication)

The resignation story had circulated as a hoax twice before it happened,
in May 2026 and again in late September to October 2026. Using the
Kompas.com fact-check publication date of 30 September 2026 as the only
observable marker: the IHSG fell 0.83 percent that day (z-score -0.86) and
EIDO fell 0.85 percent, both inside normal variation for the period, and
the 11-observation window around the marker shows a cumulative IHSG
decline of 3.58 percent that matches the prevailing downtrend rather than
any discrete reaction. There is no measurable market signature of the hoax
wave in the downloaded data.

### 4.2 Supreme Court cassation decision, 30 October 2026

The decision annulling the education equivalency letter produced only a
modest event-day move: IHSG -0.80 percent (z-score -0.23), EIDO -1.19
percent. The surrounding window is a different story: across the 11
observations from 23 October to 6 November 2026 the IHSG lost a cumulative
7.15 percent and EIDO lost 5.00 percent, while the rupiah weakened 0.86
percent and the US 10-year yield fell 12.9 basis points (a global
risk-off backdrop cannot explain the local decline, since US yields
fell). This window, not the resignation week, contains the largest
sustained repricing of Indonesian assets in the study period. The data
are consistent with investors pricing the legal and political escalation
gradually through late October rather than reacting to any single
headline.

### 4.3 HMP proposal and letter revocation, 11 November 2026

On the day 120 DPR members proposed Hak Menyatakan Pendapat and the
ministry revoked the letter, local equities were calm: IHSG -0.21 percent
(z-score 0.07), EIDO +0.10 percent. The rupiah weakened 0.45 percent
(z-score 0.64), but the dollar index itself rose 0.67 percent that day
(z-score 1.93), the largest DXY z-score of any event in the study. The
foreign exchange pressure on 11 November was primarily a global dollar
move, not an Indonesia-specific one.

### 4.4 The resignation, 12 November 2026 (main event)

- IHSG: **+2.66 percent** on the day (z-score 1.44), closing at 5,250.90,
  and a further +1.78 percent on 13 November to 5,344.41.
- EIDO: **+2.55 percent** on the day (z-score 1.10). The instrument traded
  by global investors moved in the same direction and almost the same
  size as the local index.
- DXY: +0.25 percent (z-score 0.60). The dollar was firmer, but modestly.
- US 10-year yield: **+10.5 basis points** on the day (z-score 1.88) to
  5.103 percent, the largest single-day global yield move among the study
  events. Part of the day's pressure on Indonesian assets was a global
  rates headwind, not domestic news.
- USD/IDR: the event-day return is **not computable** from the downloaded
  series because the 12 and 13 November closes are invalid ticks (see
  `data/data_sources.md`). Reported spot prints for 12 November range
  from about 18,140 to 18,250 rupiah per dollar against a valid
  11 November close of 18,140, which indicates a weaker rupiah on the day
  in spot reporting.
- Volatility: 20-day IHSG volatility printed 54.5 percent annualised on
  12 November, the maximum of the October to November period, then fell
  to 36.0 percent on 13 November and 26.6 percent by 17 November as the
  late-October crash days rolled out of the window. Volatility was a
  legacy of the October selloff more than a product of the resignation
  day itself.

## 5. Global investor decomposition

### 5.1 Global versus local pricing of the same event (EIDO against IHSG)

On 12 November, EIDO returned +2.55 percent against the IHSG's +2.66
percent, a gap of only 0.11 percentage points. Global investors, trading
in US hours, priced the resignation essentially the same way local
investors did. Over the bracket from the 11 November close to the
13 November close, the IHSG gained 4.48 percent and EIDO gained 3.82
percent. Over the longer bracket to 16 November, the IHSG gained 4.03
percent and EIDO gained 2.94 percent, a gap of 1.09 percentage points.
Part of that later gap is mechanical rather than sentiment: EIDO is
denominated in US dollars, so rupiah weakness reduces its dollar return,
and its trading hours lag Jakarta. The data show no evidence of global
investors dumping Indonesian exposure into the event; if anything they
followed the local relief move with a small lag discount.

### 5.2 Domestic versus global pressure on the rupiah

Using the nearest valid closes bracketing the event, from 11 November to
16 November 2026: USD/IDR rose 0.45 percent (rupiah weaker), while the
dollar index rose 0.62 percent over the same span. The Indonesia-specific
residual is therefore **-0.17 percentage points**: across the bracketing
span, the rupiah weakened slightly less than the broad dollar move alone
would imply. On the downloaded data there is no measurable added
Indonesia-specific currency premium across that span. This must be read
together with two reported facts that point the other way for the event
day itself: spot prints weakened on 12 November (Section 4.4), and the
reported 10-year SBN yield rose about 7.9 basis points to 7.63 percent.
The honest summary is that the currency and rates evidence is mixed and
partly rests on reporting rather than downloadable series, while the
equity evidence is consistent across two independent instruments.

### 5.3 The global backdrop

US yields rose through the event window: +10.5 basis points on
12 November and +15.6 basis points from 11 to 13 November, taking the
10-year yield to 5.154 percent. Rising US yields and a firm dollar are
the classic headwind combination for emerging market assets. Indonesian
equities rallied despite that backdrop, which strengthens the reading
that the local move was not simply a global risk-on day. It does not,
however, isolate the resignation as the cause, for the reasons in
Section 7.

## 6. Reported foreign-flow evidence

Reported figures (Kontan, cited in the Avenir research summary of
13 November 2026; stored in `data/reported_figures.csv`):

- Foreign investors were **net buyers of Rp443.53 billion** of Indonesian
  equities on 12 November 2026.
- The same investors had been **net sellers of roughly Rp127 trillion**
  from the start of 2026 to about 10 November 2026.

The single day of net buying equals about 0.35 percent of the
year-to-date net selling. It confirms the direction of the price action
(global money was not fleeing on the day) but it is far too small to
signal a regime change in foreign positioning. The structural fact of
2026 in this dataset is the outflow; the event week shows, at most, a
pause in it.

## 7. Limitations and confounders

1. **The MSCI confounder comes first.** MSCI announced its index review
   results on the same day, 12 November 2026, removing BRPT and BRMS from
   the Global Standard Index effective 1 December 2026. Index
   announcements move exactly the large, foreign-held stocks that lead
   the IHSG. No part of the 12 November rally can be attributed to the
   resignation alone.
2. **Technical rebound risk.** The IHSG had fallen 39.27 percent
   year-to-date into the event. Oversold markets bounce on any reduction
   in uncertainty, and also on short covering. The rally is consistent
   with relief, with a technical bounce, or with both.
3. **USD/IDR data quality.** The downloaded closes for the two most
   important days are invalid ticks. The event-day rupiah return cannot
   be computed from downloaded data; the study brackets it and uses
   reported spot prints, which are less precise and vary by outlet
   (18,140 to 18,250).
4. **Short post-event window.** Data end on 17 November 2026, three
   trading days after the event for the IHSG. The 60-day process to fill
   the vacancy is still running. This is an early read, not a verdict on
   the full transition.
5. **EIDO is an imperfect proxy.** It is dollar denominated, trades in US
   hours, and carries fund fees and tracking difference. Gaps against the
   IHSG partly reflect currency translation, not sentiment.
6. **No downloaded Indonesian yield series.** The SBN 10-year evidence
   (7.63 percent, up about 7.9 basis points on 12 November) comes from
   outlet reporting, not from a series this project could download and
   verify.
7. **Foreign-flow figures are reported aggregates.** Daily IDX foreign
   flow data are not freely downloadable in this environment, so flow
   evidence is limited to the two reported values above.
8. **Stressed baseline.** Z-scores use trailing 60-day volatility from a
   period containing the late-October selloff, so they understate how
   unusual the moves would look against a calm baseline.
9. **Hoax waves have no clean timestamp.** Only the 30 September 2026
   fact-check publication is used as a marker; the May 2026 wave is
   documented in the timeline but not windowed.
10. **Free data feed.** Yahoo Finance is a public aggregator, not the
    exchange. The IHSG cross-check against reported figures matched to
    the decimal on the main event day, which supports the feed for the
    equity and global series; the USD/IDR feed demonstrably failed the
    same standard and was treated accordingly.

## 8. Conclusion, bounded by the data

The downloaded data support a narrow conclusion. On the day the Vice
President resigned, Indonesian equities rose sharply in both the local
index (+2.66 percent) and the global investor instrument (+2.55
percent), and reported foreign flow was net buying. Global investors did
not price the resignation as a disorderly event. At the same time, the
currency and bond evidence available from reporting (a weaker spot
rupiah and a reported 7.9 basis point rise in the 10-year SBN yield)
shows caution in the markets that price country risk most directly, and
the downloaded FX data can neither confirm nor remove an
Indonesia-specific premium on the day itself. Because the MSCI review
landed on the same day and the market had already fallen 39.27 percent
that year, the equity rally cannot be credited to the resignation alone.
The most defensible reading is: **no panic, a measurable relief reaction
in equities shared by local and global investors, continued caution in
currency and rates, and a structural foreign outflow (about Rp127
trillion year-to-date) that one calm week does not reverse.** Whether
that holds depends on the 60-day succession process, which this dataset
ends too early to judge.
