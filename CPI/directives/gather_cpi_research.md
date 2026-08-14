# Gather CPI / Inflation Research

## Goal
Collect Eurozone and US inflation (CPI) data, derive trend and recent history, and generate a research report that feeds the AI advisor and PDF email workflow.

## Inputs
- Eurostat HICP data (euro area, all-items, annual rate of change) — no API key required
- US BLS CPI-U data (all-items, NSA for YoY, SA for MoM) — no API key required
- EUR/USD and EUR/CHF FX rates from Yahoo Finance

## Tools/Scripts
- `CPI/execution/gather_cpi_research.py` - Fetches CPI/HICP data and FX rates, computes trend, and writes a research report.
- `CPI/execution/cpi_advisor_claude.py` - Loads the research report, asks Claude for a Dutch-language narrative, renders a PDF, and emails it.

## Process
1. Load environment configuration from `.env`.
2. Fetch Eurozone HICP annual rate of change from Eurostat (`prc_hicp_manr`, geo=EA, coicop=CP00).
3. Fetch US CPI-U data from the BLS public API (series `CUUR0000SA0` for YoY, `CUSR0000SA0` for MoM).
4. Fetch EUR/USD and EUR/CHF FX rates from Yahoo Finance.
5. Compute latest value, previous value, trend (up/down/flat), and a 13-month history for each region.
6. Save a report and readable summary to `.tmp/`.
7. Run `cpi_advisor_claude.py` to generate a Dutch-language narrative, render a PDF, and email it via Gmail SMTP.

## Outputs
- `.tmp/cpi_research_report.json` - Detailed CPI/HICP data, history, and FX rates
- `.tmp/cpi_research_summary.txt` - Readable summary
- `.tmp/cpi_advisor_claude_output.txt` - Claude's Dutch narrative
- `.tmp/cpi_advisor_claude_report_<date>.pdf` - Rendered PDF report
- The PDF is emailed to `CPI_EMAIL_TO` if Gmail SMTP is configured
- Terminal output with the narrative and PDF path

## Environment Variables Required
```
ANTHROPIC_API_KEY=your_anthropic_key (for the AI narrative)
CLAUDE_MODEL=claude-opus-4-8 (optional override)
GMAIL_ADDRESS=your_gmail_address (to send the PDF)
GMAIL_APP_PASSWORD=your_gmail_app_password
CPI_EMAIL_TO=recipient@example.com
```

## Configuration
- Eurostat and BLS require no API key; both are free public statistical APIs.
- The BLS public API is rate-limited (25 queries/day per IP without a registration key) — this workflow only makes one request per run, well within that limit.
- Gmail SMTP requires an app password (not your regular Gmail password) — generate one at https://myaccount.google.com/apppasswords with 2-Step Verification enabled on the account.

## Edge Cases
- **No internet / API failure**: the script logs the failure per-source and continues with whichever source succeeded; if both fail it exits with an error.
- **Eurostat flash estimate revisions**: the latest month is often a provisional flash estimate and may be revised in a later run.
- **Missing history for YoY calc**: a month is only included in the history table once the corresponding month from a year earlier is available; a gap in official data (e.g. a US government shutdown delaying a BLS release) simply skips that period rather than failing.
- **Email not configured**: if `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD`/`CPI_EMAIL_TO` are missing, the script logs a warning and skips sending — the PDF is still generated and saved locally.
- **Missing `requests`/`reportlab`/`anthropic` libraries**: each script raises a clear message with install instructions.

## Notes
- This is a research and education tool, not financial advice.
- Review the official sources (Eurostat, BLS) directly before making any decisions based on this report.

## Walkthrough

A plain-language run-through of what happens when you run this, end to end.

**Before you start:** Eurostat and BLS need no API key. For the AI narrative, PDF, and email you'll want `ANTHROPIC_API_KEY` set, and for the email step specifically, `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` / `CPI_EMAIL_TO`. Missing the email settings is fine - the PDF still gets made, it just won't be sent anywhere.

1. **Run `python CPI/execution/gather_cpi_research.py`.**
   It fetches the latest Eurozone HICP rate from Eurostat, the US CPI-U figures from the BLS, and EUR/USD + EUR/CHF rates from Yahoo Finance - one request each, well within the BLS's free-tier limit.

2. **It crunches the numbers.**
   For each region you'll get the latest value, the previous value, a trend (up/down/flat), and a 13-month history table.

3. **Check `.tmp/`.**
   You'll find `cpi_research_report.json` (the full detailed data) and `cpi_research_summary.txt` (a quick, readable version) waiting there.

4. **Run `python CPI/execution/cpi_advisor_claude.py`.**
   This picks up the report you just generated, asks Claude to turn it into a Dutch-language narrative, and renders that into a PDF.

5. **Watch for the PDF and, if configured, the email.**
   `.tmp/cpi_advisor_claude_report_<date>.pdf` appears, and if Gmail is set up, it's emailed straight to `CPI_EMAIL_TO`. Either way, the narrative also prints to the terminal so you can read it immediately.

**If something's missing:** no email settings configured? You'll see a warning in the log, not an error - the PDF is still saved locally. One data source down (say, a delayed BLS release)? That source is skipped for the affected months rather than failing the whole run.

**You're done when:** you've got a readable Dutch-language PDF in `.tmp/` (and in your inbox, if email is set up) summarizing where Eurozone and US inflation stand this month, with trend and recent history to back it up.
