# USA Value Select Index

A rules-based equity index designed to provide systematic exposure to U.S. value stocks using a **sector-neutral value signal** across the S&P 1500 universe. The index is independently constructed, backtested over 2016–2026, and benchmarked against the S&P 1500 Composite, MSCI USA Value, and S&P 1500 Value.

---

## Overview

The USA Value Select Index selects and weights securities from the S&P 1500 based on a composite value score derived from four valuation multiples. The value signal is standardized within each GICS sector to remove structural sector-level valuation differences, making comparisons sector-relative rather than absolute. The index is reconstituted semi-annually.

---

## Index Construction Methodology

**Universe:** S&P 1500 historical constituents (~90% of US market cap), excluding Financials and Real Estate.

**Rebalancing:** Semi-annual — beginning of Q2 and Q4 each calendar year. A 60-day lag is applied to quarterly fundamental data to avoid look-ahead bias.

**Value Signals (four descriptors):**

| Signal | Formula |
|---|---|
| Earnings Yield | E / P |
| Operating Cash Flow Yield | CFO / EV |
| Book-to-Price | B / P |
| Sales-to-Price | S / P |

Each signal is cross-sectionally z-scored, then averaged into a composite value z-score per security.

**Sector-Relative Adjustment:** The composite z-score is re-standardized within each GICS sector, then winsorized at the 1st and 99th percentiles.

**Final Value Score (FVS):**
- Sector-z > 0 → FVS = 1 + sector-z
- Sector-z = 0 → FVS = 1
- Sector-z < 0 → FVS = 1 / (1 − sector-z)

**Security Selection:** Securities at or above the 70th percentile of FVS across the eligible universe are included.

**Weighting:** Free-float market cap × Final Value Score, normalized to sum to 100%.

---

## Performance Summary

### Cumulative (annualized)

| 1Y | 3Y | 5Y | 10Y |
|---|---|---|---|
| 11.07% | 14.96% | 12.61% | 9.92% |

### Calendar Year

| Year | Return | Std Dev | Return/Volatility |
|---|---|---|---|
| 2017 | 8.60% | 8.15% | 1.05 |
| 2018 | -10.58% | 16.71% | -0.63 |
| 2019 | 13.48% | 13.97% | 0.96 |
| 2020 | 10.76% | 40.06% | 0.27 |
| 2021 | 33.24% | 17.59% | 1.89 |
| 2022 | -8.97% | 21.33% | -0.42 |
| 2023 | 19.51% | 12.60% | 1.55 |
| 2024 | 14.36% | 11.78% | 1.22 |
| 2025 | 11.72% | 15.81% | 0.74 |

### Benchmark Comparison (Growth of $1, 2016–2026)

| Index | Growth |
|---|---|
| USA Value Select | 2.57x |
| MSCI USA Value | 2.51x |
| S&P 1500 Value | 2.39x |
| S&P 1500 Composite (parent) | 3.26x |

---

## Current Sector Weights

| Sector | Weight |
|---|---|
| Technology | 22.5% |
| Consumer Cyclicals | 21.4% |
| Industrials | 20.6% |
| Healthcare | 16.1% |
| Basic Materials | 7.0% |
| Energy | 5.9% |
| Utilities | 5.4% |
| Academic & Educational Services | 0.8% |
| Consumer Non-Cyclicals | 0.3% |

> Sector weights deviate from the parent index as a result of security selection and value-adjusted market cap weighting.

---

## Data Sources

| Data | Source |
|---|---|
| S&P 1500 historical constituents (quarterly) | Refinitiv API |
| Fundamental data (quarterly) | Refinitiv API (`TR.F.*` fields) |
| Daily prices | Refinitiv API |
| Free-float shares | Refinitiv API |
| Sector classification | Refinitiv TRBC Economic Sector |
| S&P 1500 Composite & Value index returns | S&P website |
| MSCI USA Value index returns | MSCI website |

---

## Tech Stack

- Python 3
- `refinitiv.data` — data ingestion
- `pandas`, `numpy` — data manipulation and signal construction
- `matplotlib` — performance charts and sector distribution
- `pickle` — caching raw data to avoid repeated API calls

---

> **Note:** Raw data files are not included. A valid Refinitiv API key is required to replicate the data collection step.

---

## Disclaimer

This project is for research and educational purposes only. It does not constitute investment advice. Past backtest performance does not guarantee future results.
