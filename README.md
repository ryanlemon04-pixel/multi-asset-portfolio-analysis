# Multi-Asset Portfolio Construction & Risk Analysis

Ryan Lemon | Independent investment research | October 2026

## Research question

Which allocation provides a defensible balance of growth, drawdowns and implementation costs for a hypothetical ten-year investor?

Compare quarterly 60/40, a fixed diversified policy and constrained minimum volatility. The backtest runs January 2008–September 2026, after 36 monthly initialization returns. The universe is SPY, EFA, IEF, GLD and SHY. SHY is a short-Treasury exposure, not cash.

## Deliverables

- `output/portfolio/Portfolio_Investment_Memo.pdf`: five-page committee memo with a recommendation, historical stress tests, reserved evaluation, costs and research limitations.
- `output/portfolio/Portfolio_Research.ipynb`: executed notebook with inspectable outputs; imports the accompanying research module.
- `inputs/portfolio/research.py`: data parsing, rolling optimization, backtesting, validation and exports.
- `inputs/portfolio/raw/`: frozen Yahoo Finance chart responses, with source endpoints and checksums in `research_results.json`.
- `output/portfolio/`: adjusted-price and asset-return CSVs, portfolio returns, allocations, results JSON and charts.
- Dashboard: an interactive hosted companion with period and portfolio controls. It uses the same precomputed results as the memo, not live market feeds.

## Main findings

After modeled costs, 60/40 returned 8.3% annually with 9.6% volatility and a 27.8% month-end maximum drawdown. Minimum volatility returned 5.9% with 6.9% volatility and an 18.1% drawdown. A fixed 40% equity control had 6.8% volatility and a 17.9% drawdown. Lower equity exposure explains much of the risk reduction; the optimizer is not shown to be unconditionally superior.

The diversified portfolio led the January 2023–September 2026 reserved evaluation but underperformed 60/40 over the full sample. The recommendation is to retain a simple growth-oriented default and offer a lower-equity policy for a tighter risk budget.

## How the calculations work

1. Convert UTC daily timestamps to New York trading dates and select month-end adjusted closes. No silent filling or missing daily prices.
2. At each quarterly rebalance, use only earlier monthly returns. The optimized policy minimizes annualized variance, with 36-month estimation and 20% shrinkage toward diagonal covariance.
3. Enforce 40–65% total equity exposure and instrument bounds at rebalance dates. Let holdings drift between trades.
4. Deduct cost before the next month's return: 5 bps times purchases plus sales. Charge initial entry. Turnover equals half the sum of traded weight changes, excluding entry for the reported annual turnover statistic.
5. Compound net returns. Calculate CAGR, monthly annualized volatility, SHY excess-return Sharpe proxy, drawdowns, recovery and turnover.
6. Compare historical stress windows, costs at 0/5/20 bps, estimation windows of 24/36/60 months and a simpler fixed 40% equity diagnostic.

Development comparison: 2008–2022. Reserved evaluation: 2023–September 2026. The whole study was designed retrospectively. Walk-forward allocations exclude future returns, but the reserved period is not a genuinely unseen prospective live test. Sensitivities do not replace the primary specification.

## Verification

Optimizer feasibility and weight sums are checked at every allocation. Removing observations after 2022 does not change earlier results. Independently recomputed wealth agrees within 4e-15. There are 261 monthly asset-return observations and 225 backtest months. Raw source checksums and validation records are in the results JSON.

## Reproduce

Extract the ZIP and preserve its folder structure. From the project root:

```bash
python3 -m pip install -r requirements.txt
python3 inputs/portfolio/research.py
python3 inputs/portfolio/build_deliverables.py
```

The second script needs DejaVu Sans system fonts at `/usr/share/fonts/truetype/dejavu/`; adapt those two paths if necessary. To use Jupyter, open `output/portfolio/Portfolio_Research.ipynb` from inside the extracted project so its root finder can locate `inputs/portfolio/research.py`. The notebook includes saved outputs and does not require network access. To recreate the charts before running its image cells, run the two commands above.

Do not refresh the raw data silently. Yahoo adjusted prices may change as subsequent distributions occur. A refreshed study needs a new timestamp, checksum manifest and revised evaluation endpoint. The historical Yahoo chart URLs and retrieval timestamp are preserved in the results audit.

## Limits

Adjusted closes approximate reinvested distribution returns, not independently reconciled official NAV total returns. The five ETFs were selected today; retrospective universe and strategy selection can bias results. Monthly drawdowns can understate daily losses. Taxes, advisory fees, nonlinear impact and execution delays are excluded. Constraints and covariance assumptions influence optimized holdings. SHY is not risk-free. A historical volatility target or drawdown is not a future guarantee.

## Interview guide

**What does the project prove?** Ability to define an investor mandate, implement chronological portfolio rules, compare risk against relevant controls and explain investment trade-offs.

**Why not just maximize historical Sharpe?** Expected returns are difficult to estimate. Searching historical combinations can produce an attractive but unstable backtest. This study fixes its primary rules and evaluates subsequent returns instead.

**What is the most important finding?** Reduced equity exposure explains much of the optimizer's drawdown reduction. The simple control matters as much as the optimizer-versus-60/40 comparison.

**Why were there losses in 2022?** Stocks and intermediate Treasuries can decline together during a rate shock. The portfolio cannot assume that bonds always offset equities.

**What does risk contribution show?** Capital weights differ from shares of variance. The diversified portfolio had about 61% equities but 78% of estimated variance from equities at September 2026 month-end.

**What is still missing?** Official NAV reconciliation, daily drawdowns, true Treasury-bill risk-free returns, taxes, a broader universe and genuinely prospective paper testing.

## Resume wording

**Multi-Asset Portfolio Construction & Risk Analysis | Python**

- Compared three stock, bond and gold allocations using a Python model with quarterly rebalancing, historical trading costs and walk-forward testing.
- Evaluated returns, volatility, drawdowns and recovery times across the 2008 financial crisis, 2020 pandemic and 2022 rate shock.
- Tested a fixed allocation against a minimum-volatility portfolio, finding that lower equity exposure explained much of the reduction in risk; presented conclusions in an investment memo and dashboard.

Use this wording once you can explain the calculations, assumptions and limitations yourself. It describes an independent work sample, not professional portfolio management experience.
