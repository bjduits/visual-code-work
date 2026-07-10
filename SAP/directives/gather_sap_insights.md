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
