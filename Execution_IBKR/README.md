# Multi-Factor Portfolio Execution — Interactive Brokers

Python script that connects to Interactive Brokers TWS via `ibapi` and automates portfolio rebalancing based on factor model output. Reads selected stocks from a CSV, exits positions no longer in the model, and places equal-weight limit orders for the new portfolio.

---

## What it does

1. Connects to TWS and loads selected stocks from the model output CSV
2. Fetches current positions and latest prices (1-min bars)
3. Liquidates holdings not in the new model selection
4. Computes equal-weight target shares with a 2% cash buffer
5. Places limit orders (±0.35% from last price) for the new portfolio

---

## Requirements

- TWS or IB Gateway running locally with socket API enabled
- Paper trading port: `7497` | Live port: `7496`

```bash
pip install ibapi pandas
```

---

## Usage

Export your factor model output to `model_stocks_selected.csv` with an `Instrument` column, then:

```bash
python MultiFactor_Execution_ibkr_RamonIslas.py
```

Update the CSV path and port in `__main__` before running. **Always test on paper trading first.**

---

## Disclaimer

For personal research only. Not investment advice. Use at your own risk.
