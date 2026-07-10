# Trading Execution Setup Guide

This guide helps you set up the short-term trading research and execution plan tools in this workspace.

## Files Created
- `Trading/directives/gather_trading_research.md`
- `Trading/execution/gather_trading_research.py`
- `Trading/execution/trading_execution_template.py`
- `Trading/execution/trading_advisor_agent.py`
- `Trading/execution/trading_advisor_claude.py`
- `Trading/execution/trading_advisor_local.py`
- `Trading/execution/market_scanner.py`
- `.tmp/trading_research_report.json`
- `.tmp/trading_research_summary.txt`
- `.tmp/trading_execution_plan.json`
- `.tmp/trading_advisor_summary.txt`
- `.tmp/trading_advisor_output.json`
- `.tmp/market_scanner_report.json`
- `.tmp/market_scanner_summary.txt`

## Step 1: Install required Python packages

Install the required `requests` and `python-dotenv` packages:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python -m pip install requests python-dotenv
```

If your system uses the Python launcher, use:

```powershell
py -3 -m pip install requests python-dotenv
```

### Optional AI advisor packages

If you want to use the AI advisor with Claude (Anthropic):

```powershell
python -m pip install anthropic
```

If you want to use a free local LLM instead:

```powershell
python -m pip install gpt4all
```

## Step 2: Configure `.env`

Open `.env` and add the following variables if they are not already present:

```text
CRYPTO_FOCUS=bitcoin,ethereum,chainlink,polkadot,solana
STOCK_FOCUS=GME,AMC,PLTR,SOFI,BB,CLNE,SPCE
NEWSAPI_KEY=
TRADING_ADVISOR_USE_AIRTABLE=1
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=TradingAdvice
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-opus-4-8
USE_LOCAL_LLM=0
GPT4ALL_MODEL_PATH=path_to_your_gpt4all_model.bin
TRADING_PLATFORM_NOTES=Coinmerce for bitcoin, Degiro.nl for stocks/minerals/metals
CURRENT_POSITIONS=BTC:25000:0.02,GME:100:10
```

- `CURRENT_POSITIONS` is optional and can pre-load held assets in the format `SYMBOL:AVG_PRICE:QUANTITY`.
- Example: `CURRENT_POSITIONS=BTC:25000:0.02,GME:100:10,ETH:1800:0.15`
- The script uses held positions to compute unrealized profit/loss and sell guidance.
- Alternatively, create `Trading/positions.json` with the same symbol/average price/quantity structure.

- `CRYPTO_FOCUS` should contain CoinGecko IDs separated by commas.
- `STOCK_FOCUS` should contain stock tickers separated by commas.
- `CRYPTO_PLATFORM` (optional) labels which platform crypto picks are meant for; defaults to `Coinmerce`.
- `STOCK_PLATFORM` (optional) labels which platform stock picks are meant for; defaults to `Degiro.nl`.
- These labels are informational only — the scripts do not verify that a given asset is actually tradeable on that platform. Only include assets in `CRYPTO_FOCUS`/`STOCK_FOCUS` that you've confirmed are available there.
- `NEWSAPI_KEY` is optional. If you have a NewsAPI key, add it to enable news headlines.
- `TRADING_ADVISOR_USE_AIRTABLE=1` enables Airtable sync.
- `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, and `AIRTABLE_TABLE_NAME` configure the Airtable destination.
- `ANTHROPIC_API_KEY` is optional if you want to use Claude instead of a local model. Get a key at `console.anthropic.com` (Settings > API Keys).
- `CLAUDE_MODEL` (optional) overrides the model used by `trading_advisor_claude.py`; defaults to `claude-opus-4-8`. Cheaper options: `claude-sonnet-5` or `claude-haiku-4-5`.
- `USE_LOCAL_LLM=1` enables the local LLM path; set `GPT4ALL_MODEL_PATH` to the model file.

## Step 3: Run the trading research script

This script gathers crypto and stock data, analyzes short-term momentum, tracks held positions, computes sell guidance, and saves the research results.

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\gather_trading_research.py
```

If Python is available via `py`, use:

```powershell
py -3 Trading\execution\gather_trading_research.py
```

## Step 4: Generate the execution plan

After the research report is generated, create a non-executing trade plan:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\trading_execution_template.py
```

This writes:
- `.tmp/trading_execution_plan.json`

## Step 5: Run the AI trading advisor and sync to Airtable

If you want AI-style advice and Airtable tracking for short-term, long-term, and risk, run:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\trading_advisor_agent.py
```

This writes:
- `.tmp/trading_advisor_summary.txt`
- `.tmp/trading_advisor_output.json`
- Airtable records if Airtable is configured

### Airtable table schema example

In Airtable, create a table with these columns:

- `Asset`
- `Name`
- `Platform`
- `Short Term (week)`
- `Long Term (6 months)`
- `Risk`
- `Score`
- `Estimated Profit %`
- `Estimated Cost %`
- `Source`

The script will populate these fields when Airtable sync is enabled.

## AI advisor options

### Claude option

1. Install `anthropic`:

```powershell
python -m pip install anthropic
```

2. Add `ANTHROPIC_API_KEY` to `.env` (get one at `console.anthropic.com` under
   Settings > API Keys). Optionally set `CLAUDE_MODEL` to override the default
   `claude-opus-4-8` (e.g. `claude-sonnet-5` or `claude-haiku-4-5` for lower cost).

3. Run the advisor:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\trading_advisor_claude.py
```

This writes `.tmp/trading_advisor_claude_output.txt`.

### Local LLM option (free, fully offline)

1. Install `gpt4all` (ships prebuilt Windows wheels, no C++ compiler needed):

```powershell
python -m pip install gpt4all
```

2. In `.env`, set `USE_LOCAL_LLM=1` and `GPT4ALL_MODEL_PATH` to an official
   gpt4all model filename (not a local file path). A good lightweight default:

```text
USE_LOCAL_LLM=1
GPT4ALL_MODEL_PATH=Llama-3.2-3B-Instruct-Q4_0.gguf
```

   The model (~1.9 GB) downloads automatically on first run and is cached
   under `~/.cache/gpt4all` -- no manual download needed. For an even
   smaller/faster model use `Llama-3.2-1B-Instruct-Q4_0.gguf`; for higher
   quality (more RAM/disk) use `Meta-Llama-3-8B-Instruct.Q4_0.gguf`. Run
   `python -c "from gpt4all import GPT4All; [print(m['filename']) for m in GPT4All.list_models()]"`
   to see the full current list.

3. Run the local advisor:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\trading_advisor_local.py
```

This writes `.tmp/trading_advisor_local_output.txt`. No API key and no
network calls to a third-party LLM provider are required -- inference runs
entirely on your machine (only the one-time model download talks to the
network).

## What each script does

- `Trading/execution/gather_trading_research.py`
  - Fetches current crypto market data from CoinGecko
  - Fetches stock quote data and 7-day history from Yahoo Finance
  - Computes momentum, volatility, and score for each asset
  - Saves a research report and summary to `.tmp/`

- `Trading/execution/trading_execution_template.py`
  - Loads the research report
  - Builds a safe candidate trade plan
  - Does not place live orders

## Step 6: Discover "hot or not" crypto and stocks beyond your watchlist

`CRYPTO_FOCUS`/`STOCK_FOCUS` only cover a fixed list of assets. To scan the
broader market for movers (trending coins, top gainers/losers, most active
stocks), run:

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python Trading\execution\market_scanner.py
```

This writes:
- `.tmp/market_scanner_report.json`
- `.tmp/market_scanner_summary.txt`

It uses CoinGecko's trending/market-cap data for crypto and Yahoo Finance's
day-gainers/day-losers/most-active screeners for stocks, then scores them
with the same momentum/risk logic as the main research script.

**Important:** this scan is intentionally unfiltered and NOT limited to
assets available on Coinmerce or Degiro.nl. Verify actual platform
availability, liquidity, and fees before acting on anything it surfaces.
Illiquid/low-cap crypto (especially "trending" coins) can also show extreme
or glitchy percentage changes from the underlying data source -- sanity
check anything that looks too good to be true.

## Notes

- This workflow is for research and planning only.
- Do not use the execution template with a live broker until you have added verified order handling and risk controls.
- Review `.tmp/trading_research_summary.txt` before considering any positions.

## Troubleshooting

- `ModuleNotFoundError: No module named 'requests'`
  - Install packages with `python -m pip install requests python-dotenv`

- `FileNotFoundError: trading_research_report.json`
  - Run `execution/gather_trading_research.py` first

- `No assets configured in CRYPTO_FOCUS or STOCK_FOCUS`
  - Update `.env` with valid asset lists
