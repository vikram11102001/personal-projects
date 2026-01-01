# 🎯 Automated Job Alert System

> **NEW!** 🚀 **Automatic API Discovery** - Just provide a company's career page URL, and the system automatically discovers and uses their job API. No manual configuration needed!

An intelligent job monitoring system that runs daily on GitHub Actions, automatically discovering job board APIs, scraping multiple companies, and sending email notifications only when new positions are found.

## ✨ Key Features

- **🔍 Automatic API Discovery**: Just add a career page URL - the system automatically discovers the API, extracts keys, and learns the format
- **🤖 Automated Daily Scraping**: Runs automatically via GitHub Actions, no manual intervention needed
- **⚡ Fast & Reliable**: Uses official job board APIs instead of fragile HTML parsing
- **🌐 Universal Compatibility**: Works with modern JavaScript-heavy job sites, with smart fallback to HTML scraping
- **📧 Smart Notifications**: Sends beautiful HTML emails only when new jobs are detected
- **💾 Persistent Storage**: Tracks job history and API configurations using Git
- **🔒 Secure**: Uses GitHub Secrets for credential management
- **📊 Intelligent Filtering**: Automatically filters by job type (intern, working student) and location (Germany)

## 🎁 What Makes This Special?

### Before (Manual API Work):
```
1. Open browser DevTools              ⏱️ 5 min
2. Find API endpoint manually         ⏱️ 10 min  
3. Extract API keys manually          ⏱️ 5 min
4. Write custom scraper code          ⏱️ 40 min
5. Test and debug                     ⏱️ 20 min
────────────────────────────────────
Total per company:                    ⏱️ 1-2 hours
```

### After (Automatic Discovery):
```python
# Just add this to config.py:
{
    "name": "Siemens",
    "url": "https://careers.siemens.com/",
    "keywords": ["intern", "internship"],
    "locations": ["Germany"]
}

# Run once - system does EVERYTHING automatically:
python3 main.py
```
```
✅ API discovered and saved           ⏱️ 30 seconds
✅ Ready to scrape automatically      ⏱️ Forever!
```

## 📁 Project Structure

```
job-finder/
├── .github/
│   └── workflows/
│       └── job-alert.yml          # GitHub Actions workflow (daily automation)
├── jobs_data/
│   └── jobs_history.json          # Historical job data (auto-updated)
├── src/
│   ├── __init__.py
│   ├── config.py                  # Simple configuration (just URLs!)
│   ├── api_discovery.py           # 🆕 Automatic API discovery module
│   ├── dynamic_api_scraper.py     # 🆕 Universal API scraper
│   ├── api_configs.json          # 🆕 Saved API configurations
│   ├── scraper.py                 # Fallback HTML scraper
│   ├── comparison.py              # Job comparison logic
│   └── email_sender.py            # Gmail SMTP notifications
├── discover_company.py            # 🆕 CLI tool to discover new company APIs
├── main.py                        # Main orchestration script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start (With Automatic API Discovery)

### 1. Generate Gmail App Password

Since Gmail requires app-specific passwords for SMTP access:

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App passwords**
4. Select app: **Mail**, Select device: **Other (Custom name)**
5. Enter a name like "Job Alert System"
6. Click **Generate**
7. **Save the 16-character password** (you'll need it in the next step)

> [!IMPORTANT]
> This is NOT your regular Gmail password. It's a special 16-character password just for this app.

### 2. Configure GitHub Secrets

Store your Gmail credentials securely in GitHub:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:
   - **Name**: `GMAIL_EMAIL`  
     **Value**: Your Gmail address (e.g., `yourname@gmail.com`)
   - **Name**: `GMAIL_APP_PASSWORD`  
     **Value**: The 16-character app password from step 1

### 3. Add Companies (Super Simple!)

Edit [`src/config.py`](src/config.py) and just add career page URLs:

```python
COMPANIES = [
    {
        "name": "MediaMarkt Saturn",
        "slug": "mediamarkt-saturn",
        "url": "https://careers.mediamarktsaturn.com/",
        "keywords": ["intern", "internship", "werkstudent"],
        "locations": ["Germany", "DEU"],
    },
    {
        "name": "Siemens",
        "url": "https://careers.siemens.com/",  # Just the base URL!
        "keywords": ["intern", "internship"],
        "locations": ["Germany"],
    },
    # Add more companies - that's it!
]
```

> [!TIP]
> No need for pre-filtered URLs, custom selectors, or API keys! The system discovers everything automatically.

### 4. Set Email Recipient

In [`src/config.py`](src/config.py), update the email recipient:

```python
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "your-email@gmail.com")
```

Alternatively, set `EMAIL_RECIPIENT` as a GitHub Secret to keep it separate from the code.

### 5. Push to GitHub

```bash
git add .
git commit -m "Initial setup of job alert system"
git push origin main
```

### 6. Enable GitHub Actions

1. Go to the **Actions** tab in your GitHub repository
2. If prompted, enable workflows for this repository
3. The workflow will run daily at 9:00 AM UTC (customizable)
4. You can also trigger it manually by clicking **Run workflow**

## 🧪 Testing Locally

Before relying on GitHub Actions, test the system locally:

### 1. Install Dependencies

```bash
cd /Users/viki/work/personal-projects/job-finder
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Environment Variables

```bash
export GMAIL_EMAIL="your-email@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"
```

### 3. Run the Script

```bash
python main.py
```

Expected output:
```
============================================================
🚀 Starting Job Alert System
============================================================

📊 Step 1: Scraping job listings...
Navigating to Google Careers page...
Found 25 job containers using selector: [class*='job']
Successfully extracted 25 jobs from Google Careers
Total jobs scraped: 25

🔍 Step 2: Comparing with historical data...
Found 25 new job(s)!

📧 Step 3: Sending email notification...
Connecting to Gmail SMTP server...
✅ Email sent successfully to your-email@gmail.com with 25 job(s)

============================================================
✅ Job Alert System completed successfully!
============================================================
```

## ⚙️ Advanced Configuration

### Custom Selectors for Specific Companies

If a company's job page has a unique structure, you can specify custom CSS selectors:

```python
{
    "name": "Custom Company",
    "url": "https://custom-company.com/careers",
    "job_container": ".custom-job-class",
    "title_selector": "h3.job-title",
    "location_selector": ".job-location",
    "link_selector": "a.apply-link"
}
```

### Customizing the Schedule

Edit [`.github/workflows/job-alert.yml`](.github/workflows/job-alert.yml) to change the cron schedule:

```yaml
schedule:
  - cron: '0 9 * * *'  # 9:00 AM UTC daily
```

Common cron patterns:
- `0 9 * * *` - Every day at 9:00 AM UTC
- `0 9 * * 1-5` - Weekdays only at 9:00 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 9,17 * * *` - Twice daily (9 AM and 5 PM UTC)

Use [crontab.guru](https://crontab.guru/) to generate custom schedules.

### Adjusting Timezone

The cron schedule uses UTC time. To convert to your local timezone:
- **9:00 AM IST** = `3:30 * * *` (UTC)
- **9:00 AM PST** = `17:00 * * *` (UTC)
- **9:00 AM EST** = `14:00 * * *` (UTC)

## 📧 Email Notification Example

When new jobs are found, you'll receive a beautifully formatted HTML email:

```
Subject: 🎯 New Job Alerts - 3 positions found

┌─────────────────────────────────────────┐
│         🎯 New Job Alerts               │
└─────────────────────────────────────────┘

Found 3 new job postings:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Google Careers
Senior Python Developer
📍 San Francisco, CA
🔗 View Job Posting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tesla Careers
Machine Learning Engineer
📍 Palo Alto, CA
🔗 View Job Posting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🔧 Troubleshooting

### No Jobs Found

1. **Check the company URL**: Visit the URL in your browser to ensure it's the careers page
2. **Inspect the page structure**: Right-click on a job listing and "Inspect Element" to see the HTML structure
3. **Add custom selectors**: Some sites require specific CSS selectors (see Advanced Configuration)
4. **Check GitHub Actions logs**: Go to Actions tab → Latest run → View logs

### Email Not Received

1. **Verify Gmail credentials**: Ensure `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` secrets are correct
2. **Check spam folder**: First emails might be filtered
3. **Review workflow logs**: Look for SMTP authentication errors in GitHub Actions
4. **Test locally**: Run the script locally to see detailed error messages

### Workflow Not Running

1. **Enable Actions**: Ensure GitHub Actions is enabled in repository settings
2. **Check branch**: Workflow file must be on the default branch (main/master)
3. **Validate YAML syntax**: Use a YAML validator to check for syntax errors
4. **Manual trigger**: Test by manually triggering from Actions tab

### Jobs History Not Updating

1. **Check Git permissions**: Ensure the workflow has write access to the repository
2. **Review commit step logs**: Look for errors in the "Commit updated job history" step
3. **Verify file path**: Ensure `jobs_data/jobs_history.json` exists

## 🛡️ Privacy & Security

- **Credentials**: Stored securely in GitHub Secrets, never exposed in code or logs
- **Email**: Sent only to your configured recipient
- **Data**: Job history stored in your private repository
- **Scraping**: Respectful delays between requests, headless browser mode

## 📊 Monitoring

### View Workflow Runs

1. Go to **Actions** tab in your repository
2. See all past runs with status (success/failure)
3. Click any run to view detailed logs

### Check Job History

The [`jobs_data/jobs_history.json`](jobs_data/jobs_history.json) file is automatically updated after each run. View it to see all tracked jobs.

## 🤝 Contributing

Feel free to customize this system for your needs:
- Add more sophisticated email templates
- Implement Slack/Discord notifications
- Add filtering by job title keywords
- Create a dashboard to visualize job trends

## 📝 License

This project is open source and available for personal use.

## 🎯 Next Steps

1. ✅ Generate Gmail App Password
2. ✅ Configure GitHub Secrets
3. ✅ Add company URLs to monitor
4. ✅ Test locally
5. ✅ Push to GitHub
6. ✅ Enable GitHub Actions
7. ✅ Wait for your first alert!

---

**Happy job hunting! 🚀**
