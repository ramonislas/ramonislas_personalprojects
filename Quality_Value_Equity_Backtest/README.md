# Quality-Value Equity Backtest

A systematic long-only equity backtest built on S&P 1500 historical constituents, combining a **Quality composite** and a **Value composite** to construct and evaluate a multi-factor portfolio against a benchmark over a 10-year period (2016–2026).

---

## Overview

This project backtests a quality-value (QV) factor strategy across the S&P 1500 universe using point-in-time fundamental data sourced from the Refinitiv API. The strategy ranks stocks quarterly using composite quality and value scores, constructs an equal-weighted portfolio of the top-ranked names, and benchmarks performance against the S&P 500.

A second portfolio (JG) is also constructed for comparison.

---

## Strategy Design

**Universe:** S&P 1500 historical constituents (2016–2026), representing ~90% of US market cap. Historical constituents are used to avoid survivorship bias.

**Sector Exclusions:** Real Estate, Financials, and Utilities are excluded due to accounting differences that make cross-sectional comparison unreliable.

**Rebalancing:** Quarterly (calendar quarter start), with SEC filing deadlines respected to avoid look-ahead bias.

**Quality Composite** (industry-adjusted z-scores, annual data from 2009):
- Profitability: Gross Profit / Total Assets
- Earnings Quality: Accruals / Total Assets
- Leverage: Net Debt / EBITDA (with overrides for negative EBITDA companies)

Weighting: 40% profitability, −20% earnings quality (accruals penalize), leverage component

**Value Composite** (quarterly data from 2014):
- Enterprise Value-based multiples (EV/EBIT, EV/Revenue, EV/FCF, P/E)
- EV calculated from market cap, debt, preferred equity, minority interest, and cash

---

## Performance & Risk Metrics

| Metric | QV Portfolio | JG Portfolio |
|---|---|---|
| Sharpe Ratio | 0.555 | 0.644 |
| 1-Day 95% VaR | 1.96% | 2.17% |
| 1-Day 95% CVaR | 3.26% | 3.46% |
| Fama-French 5 R² | 92.9% | 94.7% |
| FF5 Alpha (annualized) | Not significant | Not significant |
| Market Beta | 1.011 | 1.086 |


Additional metrics computed: annualized returns, annualized volatility, max drawdown, Sortino ratio, downside deviation, tracking error, and rolling year-by-year breakdowns for all metrics.

---

## Factor Analysis

OLS regression on Fama-French 5-factor model (Mkt-RF, SMB, HML, RMW, CMA):

- **QV Portfolio**: Strong small-cap tilt (SMB 0.770), moderate profitability exposure (RMW 0.372), mild value exposure (HML 0.120). No statistically significant alpha.
- **JG Portfolio**: Higher market beta (1.086), negative profitability exposure (RMW −0.087), strong small-cap tilt (SMB 0.644). No statistically significant alpha.

---

## Data Sources

| Data | Source |
|---|---|
| S&P 1500 historical constituents | Refinitiv API |
| Fundamental data (annual & quarterly) | Refinitiv API (`TR.F.*` fields) |
| Daily prices | Refinitiv API |
| Sector classification | Refinitiv TRBC Economic Sector |
| S&P 500 index returns | S&P website |
| Fama-French 5 factors | Kenneth French Data Library |

---

## Tech Stack

- Python 3
- `refinitiv.data` — data ingestion
- `pandas`, `numpy` — data manipulation
- `statsmodels` — OLS regression (FF5 factor model)
- `matplotlib` — visualization
- `pickle` — caching raw data to avoid repeated API calls

---


> **Note:** Raw data files are not included in this repository. A valid Refinitiv API key is required to replicate the data collection step.


## Disclaimer

This project is for research and educational purposes only. It does not constitute investment advice. Past backtest performance does not guarantee future results.
