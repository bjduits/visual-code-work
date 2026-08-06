# SAP CPI Trading Flow

## Goal
Reimplement the Trading advisor workflow (fetch market data → AI narrative → PDF → email)
entirely as a native SAP Cloud Integration (Cloud Platform Integration / CPI) integration
flow, running on its own weekday schedule, independent of the Python `Trading/` workflow
and independent of the `CPI/` inflation-report workflow (unrelated despite the shared
folder-naming coincidence with "CPI").

## Inputs
- CoinGecko market data (crypto), Yahoo Finance chart data (stocks, FX) — called directly
  from Groovy Script steps via HTTPS, no API key required
- Anthropic Claude Messages API — API key stored in CPI Security Material
- Gmail SMTP — credential stored in CPI Security Material, used by the Mail Receiver adapter

## Tools/Artifacts
- `SAP_CPI_Trading/iflow/TradingCPIFlow/` — the iFlow project source (version-controlled,
  human-readable)
- `SAP_CPI_Trading/iflow/TradingCPIFlow.zip` — the packaged import file for the SAP
  Integration Suite Web UI
- `SAP_CPI_Trading/SETUP_SAP_CPI_TRADING.md` — import and configuration instructions

## Process (inside the iFlow)
1. **Timer start event** ("Weekday Schedule") fires on the externalized cron expression
   `ScheduleCronExpression` (default: weekdays at 07:00 Europe/Amsterdam).
2. **Content Modifier** ("Set Parameters") copies externalized parameters
   (`CryptoFocus`, `StockFocus`, `ClaudeModel`, `MailFrom`, `MailTo`) onto exchange
   properties so the Script steps can read them via `message.getProperty(...)`.
3. **Script step** (`1_FetchMarketData.groovy`) fetches crypto/stock/FX data and computes
   momentum, volatility, risk, and a score per asset — a direct Groovy port of
   `Trading/execution/gather_trading_research.py`'s scoring logic.
4. **Script step** (`2_ClaudeNarrative.groovy`) builds a Dutch-language prompt from that
   data, reads the Anthropic API key from Security Material (`Anthropic_API_Key`), and
   calls the Claude Messages API for a narrative.
5. **Script step** (`3_BuildPdfReport.groovy`) renders a PDF by hand-writing PDF 1.4 syntax
   directly (no external library — see Notes).
6. **Message end event** ("Send Email") is wired via a message flow to a **Mail Receiver**
   participant, configured against Gmail SMTP with the PDF as an attachment.

## Outputs
- An emailed PDF report (`trading_cpi_report.pdf`) to `MailTo`, sent every run
- CPI Monitor message processing logs for each run (Monitor > Integrations > Manage
  Integration Content)

## Environment / Configuration Required
- Externalized parameters (set at Configure time, see `parameters.prop` for defaults):
  `CryptoFocus`, `StockFocus`, `ClaudeModel`, `MailFrom`, `MailTo`, `ScheduleCronExpression`
- Security Material (Monitor > Security Material):
  - `Anthropic_API_Key` — User Credentials, password = Anthropic API key
  - `Gmail_SMTP_Credential` — User Credentials, username = Gmail address, password = Gmail
    app password

## Edge Cases
- **Outbound HTTP blocked from Script steps by tenant policy**: the data-fetch and Claude
  calls use direct `HttpURLConnection` calls from Groovy — a common CPI pattern for public
  REST GETs, but some tenants restrict this. If blocked, replace the relevant Script logic
  with Request-Reply steps using an HTTP Receiver adapter instead.
- **Missing Security Material**: both Script steps that need a credential throw a clear
  `IllegalStateException` naming the missing artifact, visible in Monitor's error trace.
- **PDF rendering**: the PDF is hand-built without a library (see Notes) — validated
  against the same algorithm ported to Python and rendered successfully, but not yet
  round-tripped through this exact Groovy runtime.

## Notes
- This flow duplicates (rather than reuses) the scoring/narrative/PDF logic already
  written in Python for `Trading/`, by design — the point was a self-contained, native
  CPI implementation with its own schedule, so the two can run independently.
- PDF generation is hand-rolled directly against the PDF 1.4 spec because SAP CPI's
  Script step sandbox cannot load a full PDF library (e.g. iText/PDFBox) without it being
  uploaded as an "Imported Archive" resource on the iFlow. If you later add such a
  resource, `3_BuildPdfReport.groovy` can be replaced with a few lines using that library
  for a nicer-looking report (tables, styled fonts) instead of the current monospace,
  single-font layout.
- This is a research/education tool, not financial advice, same as the Python workflow.
