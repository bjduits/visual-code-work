# Trading Workflow Quick Start

This file summarizes the trading research and advisor workflow.

## Required Python packages

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python -m pip install requests python-dotenv
```

Optional packages:
```powershell
python -m pip install anthropic
python -m pip install gpt4all
```

## `.env` fields

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
```

## Run the workflow

1. Research data:
```powershell
python Trading\execution\gather_trading_research.py
```

2. Build a safe execution plan:
```powershell
python Trading\execution\trading_execution_template.py
```

3. Generate AI advisor output:
```powershell
python Trading\execution\trading_advisor_agent.py
```

4. Optional Claude summary:
```powershell
python Trading\execution\trading_advisor_claude.py
```

## Airtable schema

Create an Airtable table with these fields:
- `Asset`
- `Name`
- `Held`
- `Quantity`
- `Avg Price`
- `Unrealized %`
- `Sell Signal`
- `Short Term (week)`
- `Long Term (6 months)`
- `Risk`
- `Score`
- `Estimated Profit %`
- `Estimated Cost %`
- `Source`

To track bought assets, create `Trading/positions.json` and list entries like:
```json
{
  "BTC": {"avg_price": 25000, "quantity": 0.02},
  "GME": {"avg_price": 100, "quantity": 10}
}
```

Alternatively, set `CURRENT_POSITIONS=BTC:25000:0.02,GME:100:10` in `.env`.

The script will use these holdings to calculate unrealized profit/loss and provide sell guidance when running.

## Thematic watchlist additions (2026-08-18)

Added 10 tickers to `STOCK_FOCUS` covering geopolitical/environmental
macro themes, on top of the existing individual-stock/crypto picks. This is
a watchlist expansion only -- no new scoring logic. These assets go through
the exact same momentum + context-signal scoring as everything else; they
are not treated specially just because the underlying theme is real.

- **Water scarcity / data-center water use**: `XYL` (Xylem, water tech),
  `AWK` (American Water Works, water utility), `CGW` (Invesco S&P Global
  Water ETF), `VIE.PA` (Veolia, Paris -- water/waste, EU exposure).
- **Geopolitical tension / defense**: `LMT` (Lockheed Martin), `RTX`
  (RTX/Raytheon), `ITA` (iShares US Aerospace & Defense ETF), `RHM.DE`
  (Rheinmetall, Frankfurt -- direct European-rearmament exposure).
- **Reinsurance / climate risk pricing**: `MUV2.DE` (Munich Re, Frankfurt
  -- reinsurers reprice climate risk directly through premiums).
- **Shipping chokepoints** (Red Sea, Suez, Taiwan Strait): `MAERSK-B.CO`
  (A.P. Moller-Maersk, Copenhagen -- container shipping bellwether).

All 10 were confirmed to resolve on the Yahoo Finance endpoint this project
already uses (live price fetched successfully) before being added. Platform
availability on Degiro.nl was **not** verified -- same caveat as the rest of
`STOCK_FOCUS`, confirm before trading.

Deliberately not built: automatic buy/sell signals triggered by specific
geopolitical/weather news events. Being right that a trend is real (e.g.
"AI will use more water," "Red Sea shipping risk is structural") and being
right about *when and how hard* the market prices in a specific event are
different problems -- the timing/magnitude of a market reaction to a war,
drought, or policy shift is hard to predict mechanically even when the
underlying thesis is obviously correct. These names get the same
momentum + context scoring as everything else, not event-driven triggers.

## Evaluated and skipped: congressional trading / options-flow trackers

Checked 2026-08-18: Unusual Whales, Quiver Quantitative, Capitol Trades, and
"CommonCents" (couldn't identify a real product by this name). None have a
usable free API:

- **Unusual Whales** -- options flow and congress alerts are paywalled; API
  is a 1-week trial then $50+/mo.
- **Quiver Quantitative** -- no free API tier at all (even their paid
  website subscription excludes API access); cheapest API is $30/mo.
- **Capitol Trades** -- no official API, only unofficial scrapers.
- **House Stock Watcher / Senate Stock Watcher** (the free alternatives
  that used to cover this) are effectively dead: `housestockwatcher.com`
  no longer resolves, and the GitHub JSON archive behind Senate Stock
  Watcher hasn't been updated since December 2020.
- **Financial Modeling Prep** has Senate/House trading endpoints but they're
  gated to a paid tier, not the free 250 req/day plan.

Decision: skip congressional trading / options flow for now and stay on
free sources. Revisit only if willing to pay (~$30/mo Quiver is the
cheapest real option) -- don't re-research the free options above again,
they were a dead end as of this check.

## Market-context signals (no extra setup required)

`gather_trading_research.py` and `market_scanner.py` now pull in four
signals that are independent of an asset's own recent price action, and use
them to pull the score back down on crowded/over-extended setups (not just
push it up further on recent moves). None of these need an API key:

- **Crypto Fear & Greed Index** (alternative.me) -- extreme greed on an
  asset that already ran hard lowers its score (late-stage/crowded risk);
  extreme fear is flagged as a "don't fight the trend, but watch for
  contrarian setups" note.
- **Crypto funding rates** (Binance perpetuals) -- a strongly positive
  funding rate means longs are over-leveraged (squeeze-down risk) and lowers
  the score; a strongly negative rate flags potential short-squeeze upside.
- **VIX** (Yahoo Finance) -- an elevated VIX (>=25) applies a small
  risk-off penalty across stock scores; a very low VIX is noted as
  complacency.
- **Analyst consensus & price target** (Yahoo Finance) -- an independent,
  non-price-derived signal: a bullish analyst consensus adds to the score, a
  bearish consensus despite recent price strength is flagged as a
  divergence warning, and a price already well above the average analyst
  target is flagged as having limited upside left by that measure. Not
  available for commodity futures/ETFs (no analyst coverage).

These show up as `context_notes` on each asset in the JSON report, as
`context:` lines under each candidate in the `.txt` summaries, and as a
"Marktcontext" section plus per-asset notes in the Claude PDF report.

Funding-rate and analyst-signal lookups are per-asset network calls, so
`market_scanner.py` (which scans 100+ assets per run) only applies the two
market-wide signals (Fear & Greed, VIX) and skips the per-asset ones to
avoid hammering Binance/Yahoo; `gather_trading_research.py` (your smaller
focus list) fetches all four for every asset.

## Notes

- This workflow is research-only and does not execute trades.
- Use the AI advisor as guidance, not a signal.
- Review all summaries and platform fees before making any decisions.
- The momentum score still rewards assets for recent price strength -- by
  construction it tends to flag things that have already moved. The
  context signals above are a partial counterweight, not a fix: they don't
  make this a validated trading strategy. Nothing in this workflow tracks
  whether past "Buy" calls actually worked out -- if you want to know
  whether any of this has real edge, the highest-leverage next step is a
  scoreboard that logs each recommendation and checks its outcome days
  later, not more signals.
