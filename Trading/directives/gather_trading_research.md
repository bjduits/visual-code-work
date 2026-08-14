# Gather Short-Term Trading Research

## Goal
Collect short-term trading research inputs for crypto and small-cap stocks, analyze momentum and volatility over a 1-7 day horizon, and generate a research report.

## Inputs
- Target crypto symbols / CoinGecko IDs
- Target small-share stock tickers
- Optional NewsAPI key for headlines
- Price and volume data for short-term trend analysis

## Tools/Scripts
- `Trading/execution/gather_trading_research.py` - Main script to gather market data, analyze assets, and output a short-term research report.
- `Trading/execution/trading_execution_template.py` - Safe placeholder for building a trade plan from research results; does not execute live orders.

## Process
1. Load environment configuration from `.env`.
2. Fetch crypto market data from CoinGecko.
3. Fetch stock quote data and 7-day history from Yahoo Finance.
4. Optionally fetch market news from NewsAPI if `NEWSAPI_KEY` is configured.
5. Calculate short-term momentum, volatility, and score for each asset.
6. Create a report with candidate assets, trend notes, and next-step ideas.
7. Generate a non-executing trading plan using `execution/trading_execution_template.py`.

## Outputs
- `.tmp/trading_research_report.json` - Detailed research data
- `.tmp/trading_research_summary.txt` - Readable candidate summary
- `.tmp/trading_execution_plan.json` - Candidate trade plan generated from research
- Terminal output with top candidates and analysis notes

## Environment Variables Required
```
CRYPTO_FOCUS=bitcoin,ethereum,chainlink,polkadot,solana
STOCK_FOCUS=GME,AMC,PLTR,SOFI,BB,CLNE,SPCE
NEWSAPI_KEY=your_newsapi_key (optional)
```

## Configuration
- Adjust `CRYPTO_FOCUS` and `STOCK_FOCUS` in `.env` to reflect your trading universe.
- The system is designed for short-term research (days to one week), not long-term investing.
- Use it as a research starting point, not as automatic trade execution.

## Edge Cases
- **No internet / API failure**: the script logs the failure and continues with available sources.
- **Invalid asset symbols**: assets with missing market data are skipped and reported.
- **No NewsAPI key**: news is skipped, the script still fetches price data.
- **Missing `requests` library**: the script raises a clear message and shows install instructions.

## Notes
- This is a research tool, not trading advice.
- For live trading execution, add brokerage API integration separately and validate thoroughly.
- Review `.tmp/trading_research_summary.txt` before making any position decisions.

## Walkthrough

A plain-language run-through of what happens when you run this.

**Before you start:** set `CRYPTO_FOCUS` and `STOCK_FOCUS` in `.env` to the assets you actually care about - the defaults are just examples. `NEWSAPI_KEY` is optional; without it you still get price data, just no headlines.

1. **Run `python Trading/execution/gather_trading_research.py`.**
   It fetches crypto data from CoinGecko and stock quotes + 7-day history from Yahoo Finance for whatever's in your focus lists, plus news if you've configured `NEWSAPI_KEY`.

2. **It scores each asset.**
   Momentum, volatility, and an overall score get calculated per asset, tuned for a 1-7 day horizon rather than long-term investing.

3. **Check `.tmp/`.**
   You'll see `trading_research_report.json` (full data), `trading_research_summary.txt` (readable candidate summary), and the terminal itself prints the top candidates with notes.

4. **The script also generates a trade plan via `trading_execution_template.py`.**
   This produces `.tmp/trading_execution_plan.json` - a candidate plan built from the research, but it's a safe placeholder: nothing gets executed, no live orders are placed.

**If something's off:** an asset symbol that doesn't resolve gets skipped and reported rather than breaking the run; if an API is down entirely, the script logs it and carries on with whatever sources did respond.

**You're done when:** you've read `.tmp/trading_research_summary.txt` and have a short list of candidates with momentum/volatility notes to think about - treat it as a research starting point, not a signal to act on automatically.
