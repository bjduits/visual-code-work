# Gather SAP Insights and Render PDF

## Goal
Collect the latest SAP insights from multiple sources and render them into a PDF report, on-demand or on a schedule.

## Inputs
- Sources: SAP news, official blogs, tech publications

## Tools/Scripts
- `execution/gather_sap_insights.py` - Main script to fetch insights and render the PDF

## Process
1. **Gather insights** from configured sources:
   - NewsAPI (tech news filtered for SAP)
   - Curated SAP official sources (cloud, analytics, S/4HANA)

2. **Process insights**:
   - Remove duplicates
   - Sort by recency
   - Add source attribution

3. **Render PDF**:
   - Structured report with a numbered list of insights
   - Source and publish date per insight
   - Saved to `.tmp/sap_insights_report_<date>.pdf`

## Outputs
- PDF report at `.tmp/sap_insights_report_<date>.pdf`
- Log file tracking runs at `.tmp/sap_insights_log.txt`

## Environment Variables Required
```
NEWSAPI_KEY=your_newsapi_key (optional, free tier available)
```

## Configuration
- **Update frequency**: Daily, weekly, or on-demand (configurable via scheduler)
- **Minimum sources**: 2+ for redundancy
- **Batch size**: Top 10 insights per run

## Edge Cases
- **No new insights found**: PDF still generated with a "no updates" note
- **API failures**: Fall back to curated built-in sources, log error
- **Rate limits**: Implement caching and respect API limits

## Notes
- No email/SMTP dependency — output is a local PDF file only
- Can be scheduled via Windows Task Scheduler or cron
- Logs stored in `.tmp/sap_insights_log.txt`

## Walkthrough

A plain-language run-through of what happens when you run this.

**Before you start:** no API key is strictly required — `NEWSAPI_KEY` is optional and only widens the news sources. Without it, the script still runs on the curated SAP sources.

1. **Run `python execution/gather_sap_insights.py`.**
   The script starts pulling from its configured sources: SAP news, official blogs, and tech publications (plus NewsAPI if you've set a key).

2. **It cleans up what it found.**
   Duplicates are removed, everything is sorted by recency, and each insight gets a source + publish date attached.

3. **It renders a PDF.**
   You'll see a structured, numbered report take shape - each insight with its source and date - written to `.tmp/sap_insights_report_<date>.pdf`.

4. **Check the terminal and the log.**
   The terminal prints where the PDF landed. A run log is appended to `.tmp/sap_insights_log.txt` so you can see history across runs.

**If something goes sideways:** a source that's down doesn't stop the run - the script falls back to the curated built-in sources and logs the failure instead of crashing. If literally nothing new was found, you still get a PDF, just with a "no updates" note instead of an empty file.

**You're done when:** `.tmp/sap_insights_report_<date>.pdf` opens and shows a readable, dated list of SAP insights with sources - ready to skim or forward.
