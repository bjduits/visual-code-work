# CPI / Inflation Workflow Setup Guide

This guide sets up a monthly CPI/inflation research workflow, modeled on the
`Trading` workflow: gather data → generate an AI narrative → render a PDF →
email it.

## Files Created
- `CPI/directives/gather_cpi_research.md` - Full SOP documentation
- `CPI/execution/gather_cpi_research.py` - Fetches Eurozone HICP + US CPI + FX rates
- `CPI/execution/cpi_advisor_claude.py` - Claude narrative, PDF rendering, and email send
- `.tmp/cpi_research_report.json`, `.tmp/cpi_research_summary.txt`
- `.tmp/cpi_advisor_claude_output.txt`, `.tmp/cpi_advisor_claude_report_<date>.pdf`

## Step 1: Install required Python packages

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python -m pip install requests python-dotenv reportlab anthropic
```

`requests`, `python-dotenv`, and `reportlab` are required. `anthropic` is
required for the narrative step (`cpi_advisor_claude.py`); the research
gathering step (`gather_cpi_research.py`) does not need it.

## Step 2: Configure `.env`

The following keys were already appended to your `.env` (fill in the blanks):

```text
ANTHROPIC_API_KEY=          # reused from the Trading workflow if already set
CLAUDE_MODEL=claude-opus-4-8  # reused from the Trading workflow if already set
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
CPI_EMAIL_TO=bjduits@gmail.com
```

- `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` are shared with the Trading workflow — if
  you already configured these for `Trading/execution/trading_advisor_claude.py`,
  nothing more to do here.
- `GMAIL_ADDRESS` — the Gmail account the report is sent *from*.
- `GMAIL_APP_PASSWORD` — a 16-character Gmail **app password**, not your normal
  Gmail password:
  1. Enable 2-Step Verification on the Google account: https://myaccount.google.com/security
  2. Create an app password at https://myaccount.google.com/apppasswords
  3. Paste the generated 16-character password into `.env`
- `CPI_EMAIL_TO` — recipient address (defaults to `bjduits@gmail.com`, already set).

If `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` are left blank, the workflow still runs
and still writes the PDF to `.tmp/` — it just skips the email step and logs a
warning.

## Step 3: Run the research script

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python CPI\execution\gather_cpi_research.py
```

This writes:
- `.tmp/cpi_research_report.json`
- `.tmp/cpi_research_summary.txt`

No API key is required for this step — Eurostat and the BLS public API are
both free and keyless.

## Step 4: Run the AI advisor, generate the PDF, and email it

```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python CPI\execution\cpi_advisor_claude.py
```

This writes:
- `.tmp/cpi_advisor_claude_output.txt` (Dutch narrative)
- `.tmp/cpi_advisor_claude_report_<date>.pdf`
- Emails the PDF to `CPI_EMAIL_TO` if Gmail SMTP is configured

## Step 5: Schedule it monthly (Task Scheduler)

Eurostat's HICP flash estimate and the US BLS CPI report are both typically
published by the middle of the month for the prior month. Running on the
20th gives both sources time to publish.

1. Open Task Scheduler
2. Create Basic Task named "CPI Inflation Report"
3. Trigger: Monthly, day 20, at a time of your choosing (e.g. 08:00)
4. Action 1: Run program
   - Program: `python.exe`
   - Arguments: `C:\Users\Bram-JanDuits\visual-code-work\CPI\execution\gather_cpi_research.py`
   - Start in: `C:\Users\Bram-JanDuits\visual-code-work`
5. Add a second action (Task Properties > Actions > New) so both scripts run
   in the same job:
   - Program: `python.exe`
   - Arguments: `C:\Users\Bram-JanDuits\visual-code-work\CPI\execution\cpi_advisor_claude.py`
   - Start in: `C:\Users\Bram-JanDuits\visual-code-work`

Task Scheduler runs multiple actions in order, so the research step always
completes before the advisor/PDF/email step reads its output.

## What each script does

- `CPI/execution/gather_cpi_research.py`
  - Fetches Eurozone HICP (annual % change) from Eurostat
  - Fetches US CPI-U (YoY from the NSA series, MoM from the SA series) from the BLS API
  - Fetches EUR/USD and EUR/CHF FX rates from Yahoo Finance
  - Computes trend and a 13-month history for each region
  - Saves a research report and summary to `.tmp/`

- `CPI/execution/cpi_advisor_claude.py`
  - Loads the research report
  - Asks Claude for a Dutch-language narrative grounded only in the fetched figures
  - Renders a PDF with a summary table, history tables, and the narrative
  - Emails the PDF as an attachment via Gmail SMTP (skips gracefully if not configured)

## Troubleshooting

- `FileNotFoundError: cpi_research_report.json`
  - Run `gather_cpi_research.py` first
- `ModuleNotFoundError: No module named 'requests'` / `'reportlab'` / `'anthropic'`
  - Install with `python -m pip install requests python-dotenv reportlab anthropic`
- Email not arriving
  - Check `.tmp/cpi_advisor_claude.log` for a warning or SMTP error
  - Confirm `GMAIL_APP_PASSWORD` is an app password, not the regular account password
  - Gmail app passwords require 2-Step Verification to be enabled first
- `BLS API request did not succeed`
  - The public BLS API is limited to 25 queries/day per IP; this workflow only
    uses one request per run, so this is rare — retry later if it happens

## Notes

- This workflow is for research and education only, not financial advice.
- Eurostat's latest month is often a provisional flash estimate and may be revised later.
- Review the official sources (Eurostat, BLS) directly before acting on anything in the report.
