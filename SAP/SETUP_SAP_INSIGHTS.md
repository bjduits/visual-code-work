# SAP Insights Setup Guide

## Quick Start

Your SAP insights solution renders a local PDF report — no email/SMTP setup required.

### Step 1: (Optional) Add NewsAPI for Better Coverage

1. Get free API key: https://newsapi.org/register
2. Add to `.env`:
   ```
   NEWSAPI_KEY=your_newsapi_key
   ```

### Step 2: Install dependencies

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python -m pip install requests python-dotenv reportlab
```

### Step 3: Run the script

```powershell
python SAP\execution\gather_sap_insights.py
```

Check that:
- A PDF appears at `SAP\.tmp\sap_insights_report_<date>.pdf`
- No errors in terminal
- Log file created at `SAP\.tmp\sap_insights_log.txt`

### Step 4: Schedule It (Optional)

To run automatically, create a Windows Task Scheduler job:

1. Open Task Scheduler
2. Create Basic Task named "SAP Insights"
3. Set trigger (Daily at 9 AM, etc.)
4. Set action: Run program
   - Program: `python.exe`
   - Arguments: `C:\Users\Bram-JanDuits\visual-code-work\SAP\execution\gather_sap_insights.py`
   - Start in: `C:\Users\Bram-JanDuits\visual-code-work`

## Files Created

- **Directive**: `SAP/directives/gather_sap_insights.md` - Full SOP documentation
- **Script**: `SAP/execution/gather_sap_insights.py` - The main execution engine
- **Config**: `.env` - Your `NEWSAPI_KEY` (optional)
- **Logs**: `.tmp/sap_insights_log.txt` - Execution history
- **Output**: `.tmp/sap_insights_report_<date>.pdf` - The rendered report

## What It Does

Each run:
1. Gathers insights from multiple sources (NewsAPI, curated SAP sources)
2. Deduplicates and sorts by recency
3. Renders a PDF report
4. Logs all activity

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found: requests" | Run `pip install requests` |
| "Module not found: reportlab" | Run `pip install reportlab` |
| No insights in report | NewsAPI might be down or `NEWSAPI_KEY` not set; built-in sources are used as fallback |

## Next Steps

- Modify `directives/gather_sap_insights.md` to customize sources
- Add more data sources in `execution/gather_sap_insights.py`
- Schedule it to run automatically

---

**Questions?** Check the directive file for detailed documentation on how the system works.
