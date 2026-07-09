# SAP Insights Setup Guide

## Quick Start

Your SAP insights solution is ready! Follow these steps to activate it:

### Step 1: Configure Gmail (Required)

The system sends emails via Gmail. You need to:

1. **Use Gmail App Password** (recommended for security):
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification" if not already enabled
   - Go to "App passwords" section
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

2. **Update `.env` file**:
   ```
   GMAIL_ADDRESS=your_actual_gmail@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_password
   RECIPIENT_EMAIL=bjduits@gmail.com
   ```

### Step 2: (Optional) Add NewsAPI for Better Coverage

1. Get free API key: https://newsapi.org/register
2. Add to `.env`:
   ```
   NEWSAPI_KEY=your_newsapi_key
   ```

### Step 3: Test the Solution

Run the script:
```powershell
cd c:\Users\Bram-JanDuits\visual-code-work
python SAP\execution\gather_sap_insights.py
```

Check that:
- Email arrives at `bjduits@gmail.com`
- No errors in terminal
- Log file created at `.tmp/sap_insights_log.txt`

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
- **Config**: `.env` - Your credentials and API keys
- **Logs**: `.tmp/sap_insights_log.txt` - Execution history

## What It Does

Each run:
1. ✅ Gathers insights from multiple sources (NewsAPI, SAP official, tech news)
2. ✅ Deduplicates and filters for relevance
3. ✅ Formats into a beautiful HTML email
4. ✅ Sends to your email address
5. ✅ Logs all activity

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Authentication failed" | Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in `.env` |
| "Module not found: requests" | Run `pip install requests` |
| "Module not found: python-dotenv" | Run `pip install python-dotenv` |
| No email received | Check spam folder, verify RECIPIENT_EMAIL in `.env` |
| Script runs but no insights | NewsAPI might be down; built-in sources are used as fallback |

## Next Steps

- Modify `directives/gather_sap_insights.md` to customize sources
- Add more data sources in `execution/gather_sap_insights.py`
- Schedule it to run automatically
- Adjust filtering logic based on your preferences

---

**Questions?** Check the directive file for detailed documentation on how the system works.
