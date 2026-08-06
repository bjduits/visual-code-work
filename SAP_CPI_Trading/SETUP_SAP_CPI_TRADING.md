# SAP CPI Trading Flow — Setup Guide

This is a **separate, self-contained trading setup** built natively in SAP Cloud
Integration (CPI), running alongside — not replacing — the existing Python-based
`Trading/` workflow. It has its own schedule, its own Groovy-based logic, and its own
email delivery via a Mail Receiver adapter.

> **Naming note:** this has nothing to do with the `CPI/` folder elsewhere in this repo,
> which is a Consumer Price Index / inflation report (a naming collision from an earlier
> misunderstanding of "CPI" in this conversation). This folder, `SAP_CPI_Trading/`, is the
> SAP Cloud Platform Integration trading flow.

## Important: read this before importing

I originally hand-authored the `.iflw` XML from memory, and the first import attempt
failed with a `500` from `.../iflows`. To fix it properly, we pulled a **real blank iFlow
export from your own trial tenant** (Web UI → Create blank flow → Download) and diffed it
against mine. That surfaced several concrete bugs, now fixed:
- `MANIFEST.MF` had the wrong `SAP-NodeType` (`IFlow` instead of the correct `IFLMAP`) and
  was missing the required `Import-Package` block and `Bundle-ManifestVersion`.
- `.project` had the wrong Eclipse nature entirely.
- The Collaboration and Process extension elements were missing their `cmdVariantUri`
  (component variant identifiers) and other required properties that every real element
  carries.
- `<bpmn2:definitions>` was missing the required `targetNamespace`/`name` attributes.

The current `.iflw`/`MANIFEST.MF`/`.project` are now built as a mechanical extension of
that verified real export, changing as little of the known-working skeleton as possible.
This removes most of the risk — but a few pieces still couldn't be verified against real
tenant data because the blank sample doesn't use them:
- The **Timer start event**'s exact `cmdVariantUri` (`CronTimer`) and the **Mail Receiver
  adapter**'s exact connection field names/values — both are my best-effort reconstruction
  from general CPI conventions, not confirmed against your tenant.
- The Groovy scripts haven't executed in a real CPI runtime (only the PDF-building
  *algorithm* was validated, by porting it to Python and rendering real output — see
  Notes below).

**If this import still fails**, get the Network tab response body for the `500` (see the
troubleshooting note at the end) and we'll fix the next concrete thing rather than guess
again.

## Files

- `iflow/TradingCPIFlow/` — the iFlow project source, readable/diffable in git
- `iflow/TradingCPIFlow.zip` — **the import file** — upload this in the Web UI
- `directives/sap_cpi_trading_flow.md` — SOP documentation

## Step 1: Import the flow

1. Open SAP Integration Suite → Design → your Integration Package (or create a new one,
   e.g. "Trading Flows").
2. Open the package → **Edit** → **Add** → **Integration Flow** → **Upload**.
3. Select `SAP_CPI_Trading/iflow/TradingCPIFlow.zip`.
4. Save the package.
5. Open `TradingCPIFlow` in the graphical editor and confirm it opens without errors. If
   the canvas fails to render or shows a validation error, it's most likely the Mail
   Receiver step (see Step 4) — everything else should be straightforward to fix from the
   editor directly if needed.

## Step 2: Create Security Material

Monitor → Security Material → Create:

1. **Anthropic_API_Key**
   - Type: User Credentials
   - User: anything (e.g. `anthropic`)
   - Password: your Anthropic API key (from console.anthropic.com → Settings → API Keys)

2. **Gmail_SMTP_Credential**
   - Type: User Credentials
   - User: your Gmail address
   - Password: a Gmail **app password** (not your normal password) — enable 2-Step
     Verification on the account, then generate one at
     https://myaccount.google.com/apppasswords

## Step 3: Configure externalized parameters

Open the imported iFlow → **Configure**, and set:

| Parameter | Default | What to set it to |
|---|---|---|
| `CryptoFocus` | `bitcoin,ethereum,chainlink,polkadot,solana` | Your crypto watchlist (CoinGecko IDs) |
| `StockFocus` | `GME,AMC,PLTR,SOFI,BB,CLNE,SPCE` | Your stock watchlist (tickers) |
| `ClaudeModel` | `claude-opus-4-8` | Or a cheaper model, e.g. `claude-sonnet-5` |
| `MailFrom` | `your.gmail.address@gmail.com` | The Gmail address matching `Gmail_SMTP_Credential` |
| `MailTo` | `bjduits@gmail.com` | Recipient address |
| `ScheduleCronExpression` | `0 0 7 ? * MON-FRI *` | Weekdays at 07:00 Europe/Amsterdam — edit if you want a different time |

## Step 4: Verify the Mail Receiver step

Open the "Send Email" end event's connected Mail Receiver participant → Connection tab,
and confirm/re-enter:
- Host: `smtp.gmail.com`, Port: `465`, protocol: SMTPS
- Authentication: User Credentials → `Gmail_SMTP_Credential`
- From: `{{MailFrom}}`, To: `{{MailTo}}`
- Attachment: enabled, filename `trading_cpi_report.pdf`, content type `application/pdf`

This is the one part of the hand-authored flow most likely to need re-entering through the
UI's own dropdowns/fields rather than trusting the imported values verbatim.

## Step 5: Deploy and test

1. Save and **Deploy** the iFlow.
2. In Monitor → Manage Integration Content, find `TradingCPIFlow` and trigger a manual
   test run if the tenant supports ad-hoc Timer triggering, or temporarily set
   `ScheduleCronExpression` to a few minutes in the future to confirm an end-to-end run.
3. Check Monitor → Message Processing Logs for the run. Common failure points to check
   first if it errors:
   - **Fetch Market Data / Ask Claude for Narrative fail with a network error**: your
     tenant's script sandbox may block outbound HTTP from Groovy — see the directive's
     Edge Cases section for the Request-Reply/HTTP Receiver adapter alternative.
   - **Ask Claude for Narrative fails with "Security Material ... not found"**: the
     credential name in Security Material doesn't exactly match `Anthropic_API_Key`.
   - **No email arrives**: check the Mail Receiver step's trace in the message log; verify
     the Gmail app password and that `MailFrom` matches the credential's username.
   - **PDF looks broken/won't open**: this is the one component I couldn't test inside a
     real CPI runtime — see the Notes below for the fallback.

## If PDF generation doesn't render correctly

`3_BuildPdfReport.groovy` hand-writes raw PDF 1.4 syntax (objects, content streams, xref
table) because CPI's script sandbox doesn't have a PDF library available by default. I
validated the exact same algorithm in Python and confirmed it renders correctly, but this
hasn't been round-tripped through an actual CPI/Groovy execution. If it produces a
malformed PDF in your tenant:

1. Check Monitor's trace for the byte length written vs. what a PDF viewer reports as
   corrupted — a mismatch usually means a Groovy-vs-Python string encoding subtlety.
2. The more robust production fix: add a real PDF library (e.g. **OpenPDF**, a maintained
   iText fork under LGPL/MPL) as an **Imported Archive** resource on the iFlow
   (Design → Resources → Add → Archive), then rewrite `3_BuildPdfReport.groovy` to use it
   directly — a handful of lines instead of the current hand-rolled byte construction.

## Notes

- This flow is independent of `Trading/` (Python) and `CPI/` (inflation reports) — nothing
  here reads or writes their `.tmp/` files or `.env` values.
- This is a research/education tool, not financial advice.
