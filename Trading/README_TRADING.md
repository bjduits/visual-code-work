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

## Notes

- This workflow is research-only and does not execute trades.
- Use the AI advisor as guidance, not a signal.
- Review all summaries and platform fees before making any decisions.
