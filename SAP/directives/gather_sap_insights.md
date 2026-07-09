# Gather SAP Insights and Email

## Goal
Collect the latest SAP insights from multiple sources and send them to the user via email on a scheduled basis or on-demand.

## Inputs
- Recipient email: `bjduits@gmail.com`
- Sources: SAP news, official blogs, tech publications
- Schedule: Can be run manually or via scheduler

## Tools/Scripts
- `execution/gather_sap_insights.py` - Main script to fetch insights and send email

## Process
1. **Gather insights** from configured sources:
   - NewsAPI (tech news filtered for SAP)
   - SAP official blog and announcements
   - Tech news websites (TechCrunch, TheNextBig Thing, etc.)
   - LinkedIn SAP thought leaders

2. **Process insights**:
   - Remove duplicates
   - Filter for relevance
   - Sort by recency and importance
   - Add source attribution

3. **Format email**:
   - Structured HTML layout with categories
   - Links to full articles
   - Brief summary for each insight
   - Date and source information

4. **Send email**:
   - Use SMTP (Gmail with app password recommended)
   - Track delivery

## Outputs
- Email sent to recipient with latest SAP insights
- Log file tracking runs and delivery status

## Environment Variables Required
```
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
RECIPIENT_EMAIL=bjduits@gmail.com
NEWSAPI_KEY=your_newsapi_key (optional, free tier available)
```

## Configuration
- **Update frequency**: Daily, weekly, or on-demand (configurable)
- **Minimum sources**: 3+ for redundancy
- **Batch size**: Top 5-10 insights per category
- **Retry attempts**: 3 attempts with exponential backoff on failure

## Edge Cases
- **No new insights found**: Send notification indicating no new updates
- **API failures**: Fall back to other sources, log error
- **Email delivery failure**: Retry with exponential backoff
- **Rate limits**: Implement caching and respect API limits

## Notes
- First run requires setting up `.env` with email credentials
- Recommend using Gmail app password (more secure than account password)
- Can be scheduled via Windows Task Scheduler or cron
- Logs stored in `.tmp/sap_insights_log.txt`
