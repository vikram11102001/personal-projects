# LinkedIn AI/ML Job Agent — Setup Guide 🤖🇩🇪

> **Automated daily LinkedIn job scraper** that emails AI & ML internship, part-time, and Werkstudent listings in Germany.
> **100% free** — no paid APIs, no LinkedIn account needed.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Agent](#running-the-agent)
- [Email Output](#email-output)
- [Hosting Options (Free)](#hosting-options-free)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)
- [FAQ](#faq)

---

## Overview

This agent runs on a daily schedule and:

1. **Scrapes LinkedIn** public job listings for AI/ML roles in Germany (no login required)
2. **Deduplicates** results using a local SQLite database — your friend only gets NEW jobs
3. **Sends a formatted HTML email** via Gmail SMTP with job title, company, location, type, and apply link
4. **Falls back gracefully** — if no new jobs are found today, sends trending jobs from recent history with a friendly message

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────┐
│  Scheduler  │────▶│ LinkedIn Scraper │────▶│  SQLite DB    │────▶│ Email Builder│────▶│  Gmail   │
│  (daily)    │     │  (BeautifulSoup) │     │  (dedup/store)│     │  (HTML+Text) │     │  (SMTP)  │
└─────────────┘     └──────────────────┘     └───────────────┘     └──────────────┘     └──────────┘
```

**Flow:**
- `schedule` library triggers the job at a set time each day
- `requests` + `BeautifulSoup` scrape LinkedIn's public job search
- `sqlite3` stores all seen job IDs to avoid duplicate emails
- `smtplib` sends the digest via Gmail's free SMTP server

---

## Tech Stack

| Tool | Purpose | Cost |
|---|---|---|
| `Python 3.8+` | Runtime | Free |
| `requests` | HTTP scraping | Free |
| `beautifulsoup4` | HTML parsing | Free |
| `schedule` | Daily cron-like scheduler | Free |
| `lxml` | Fast XML/HTML parser | Free |
| `sqlite3` | Job deduplication database | Free (built-in) |
| `smtplib` | Email sending | Free (built-in) |
| Gmail SMTP | Email delivery | Free |

**Total cost: $0**

---

## Project Structure

```
linkedin-job-agent/
├── job_agent.py              # Main agent (scraper + emailer + scheduler)
├── config.py                 # ✏️  Edit this — your email & schedule settings
├── requirements.txt          # Python dependencies
├── run.sh                    # One-click setup & launch script (Mac/Linux)
├── linkedin-job-agent.service # systemd service file (Linux background service)
├── jobs.db                   # SQLite DB — auto-created on first run
└── logs/
    └── agent.log             # Daily activity log
```

---

## Prerequisites

- **Python 3.8 or higher**
- **A Gmail account** (for sending emails)
- **Internet connection** (for scraping LinkedIn)

Check your Python version:

```bash
python3 --version
```

---

## Installation

### Step 1 — Download the project

```bash
# If cloning from GitHub
git clone https://github.com/your-username/linkedin-job-agent.git
cd linkedin-job-agent
```

### Step 2 — Create a virtual environment (recommended)

```bash
# Create the venv
python3 -m venv venv

# Activate it
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt contents:**

```
requests==2.31.0
beautifulsoup4==4.12.3
schedule==1.2.1
lxml==5.1.0
```

---

## Configuration

### Step 1 — Generate a Gmail App Password

> ⚠️ You must use an **App Password**, not your regular Gmail password.

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required)
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Select **Mail** → **Other (custom name)** → type `JobAgent`
5. Click **Generate** → copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

> 💡 The App Password is shown **only once** — copy it immediately.

---

### Step 2 — Edit `config.py`

Open `config.py` and fill in your values:

```python
CONFIG = {
    # Gmail address that SENDS the email
    "sender_email": "yourgmail@gmail.com",

    # The 16-character App Password from Step 1 above
    "gmail_app_password": "abcd efgh ijkl mnop",

    # Your friend's email in Germany (where jobs will be delivered)
    "recipient_email": "friend@example.com",

    # Time to send each day (24-hour format, machine local time)
    "schedule_time": "08:00",

    # How many trending jobs to show when no new jobs are found
    "top_jobs_count": 8,

    # Max new jobs per email
    "max_new_jobs_per_email": 20,
}
```

> 💡 **Tip:** The sender and recipient can be the same Gmail address — just use your friend's Gmail for both and generate the App Password from her Google account.

---

## Running the Agent

### Option A — Simple (stays in terminal)

```bash
python3 job_agent.py
```

On first run it will:
1. Run an immediate scrape + send the first email
2. Then wait and re-run daily at your `schedule_time`

### Option B — Background process (Mac/Linux)

```bash
nohup python3 job_agent.py > logs/agent.log 2>&1 &

# Check if it's running
ps aux | grep job_agent

# View live logs
tail -f logs/agent.log
```

### Option C — Use the setup script

```bash
bash run.sh
```

This checks for Python, creates a venv, installs deps, verifies config, and starts the agent.

### Option D — systemd service (Linux, runs on boot)

```bash
# 1. Edit the .service file — update the WorkingDirectory and ExecStart paths
nano linkedin-job-agent.service

# 2. Copy to systemd
sudo cp linkedin-job-agent.service /etc/systemd/system/

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable linkedin-job-agent
sudo systemctl start linkedin-job-agent

# 4. Check status
sudo systemctl status linkedin-job-agent
```

---

## Email Output

### When new jobs are found

The email includes:
- **Header** with today's date and job count
- **Stats bar** — new jobs count, job types, country
- **New jobs section** — each card shows:
  - Job title (clickable → LinkedIn)
  - Company name
  - Location in Germany
  - Job type badge (Internship / Working Student / Part-time)
  - Apply button

### When no new jobs are found

The email includes:
- A friendly "No new jobs today" notice
- **Trending section** — 8 recent jobs from the database as "companies hiring actively"

---

## Hosting Options (Free)

To run the agent 24/7 without keeping your laptop on:

### Render.com (Recommended)

1. Push the project to a GitHub repo
2. Go to [render.com](https://render.com) → New → **Background Worker**
3. Connect your repo
4. Set **Build Command:** `pip install -r requirements.txt`
5. Set **Start Command:** `python3 job_agent.py`
6. Set environment variables for `SENDER_EMAIL`, `GMAIL_APP_PASSWORD`, `RECIPIENT_EMAIL`
7. Deploy — it runs forever on the free tier

> 💡 If using Render, update `config.py` to read from `os.environ`:
> ```python
> import os
> CONFIG = {
>     "sender_email":       os.environ.get("SENDER_EMAIL"),
>     "gmail_app_password": os.environ.get("GMAIL_APP_PASSWORD"),
>     "recipient_email":    os.environ.get("RECIPIENT_EMAIL"),
>     "schedule_time":      os.environ.get("SCHEDULE_TIME", "08:00"),
> }
> ```

### Railway.app

1. Push to GitHub → connect to [railway.app](https://railway.app)
2. Add environment variables in the dashboard
3. Start command: `python3 job_agent.py`
4. Free $5 credits/month — more than enough for this agent

### Raspberry Pi (home server)

```bash
# On your Pi, clone the repo and set up the systemd service (Option D above)
# The Pi uses ~3W of power — essentially free to run
```

---

## Troubleshooting

### ❌ No jobs are being scraped

LinkedIn occasionally updates their HTML structure. Check the logs:

```bash
tail -f logs/agent.log
```

If you see `0 jobs found` for all queries, LinkedIn may have changed their page layout. Open an issue or update the CSS selectors in `job_agent.py` inside the `scrape_linkedin()` function.

---

### ❌ Email not sending

**Check 1** — Make sure 2-Step Verification is ON in your Google account.

**Check 2** — Confirm the App Password is correct in `config.py` (no extra spaces).

**Check 3** — Test manually:

```python
import smtplib
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login("yourgmail@gmail.com", "your app password")
    print("✅ Login successful")
```

**Check 4** — Some corporate Gmail accounts block SMTP. Use a personal Gmail instead.

---

### ❌ `ModuleNotFoundError`

Make sure your virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

### ❌ Agent stops after one run

The `schedule` loop requires the process to stay alive. Use `nohup`, `tmux`, `screen`, or a systemd service to keep it running.

---

## Customization

### Change job search queries

In `job_agent.py`, find the `SEARCH_QUERIES` list and edit it:

```python
SEARCH_QUERIES = [
    ("Artificial Intelligence Intern Germany",    "Internship"),
    ("Machine Learning Intern Germany",           "Internship"),
    ("AI Werkstudent Germany",                    "Working Student"),
    ("Deep Learning Intern Germany",              "Internship"),     # ← add more
    ("MLOps Intern Germany",                      "Internship"),     # ← add more
    # ... add or remove as needed
]
```

### Change the schedule time

In `config.py`:

```python
"schedule_time": "09:30",   # Send at 9:30 AM every day
```

### Change the target country

In `scrape_linkedin()`, update the `location` parameter:

```python
params = {
    "location": "Germany",  # Change to "Netherlands", "Austria", etc.
    ...
}
```

### Run multiple times a day

In `job_agent.py`, replace the single `schedule` line:

```python
# Instead of:
schedule.every().day.at(CONFIG["schedule_time"]).do(run_daily_job)

# Use:
schedule.every().day.at("08:00").do(run_daily_job)
schedule.every().day.at("18:00").do(run_daily_job)
```

---

## FAQ

**Q: Does this require a LinkedIn account?**
No. It scrapes LinkedIn's public job search pages — the same pages visible when you search LinkedIn without logging in.

**Q: Will LinkedIn block the scraper?**
The agent includes polite delays between requests (2–4 seconds) and a realistic browser User-Agent header. For personal daily use at this frequency, it works reliably. If you increase frequency significantly, LinkedIn may rate-limit your IP.

**Q: Can I use a non-Gmail email?**
Yes — update the SMTP settings in `job_agent.py`:
```python
# For Outlook / Hotmail
with smtplib.SMTP("smtp.office365.com", 587) as server:
    server.starttls()
    server.login(...)
```

**Q: How do I see which jobs are in the database?**
```bash
sqlite3 jobs.db "SELECT title, company, location, date_found FROM jobs ORDER BY date_found DESC LIMIT 20;"
```

**Q: How do I reset the database (resend all jobs)?**
```bash
rm jobs.db
python3 job_agent.py   # Will recreate and treat all jobs as new
```

**Q: Can I deploy this on GitHub Actions (free)?**
Yes — create a `.github/workflows/job_agent.yml` with a cron trigger. Store your email credentials as GitHub Secrets.

```yaml
name: Daily Job Scrape
on:
  schedule:
    - cron: '0 7 * * *'   # 7 AM UTC daily
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python3 job_agent.py --run-once   # Add a --run-once flag to skip scheduler
        env:
          SENDER_EMAIL:        ${{ secrets.SENDER_EMAIL }}
          GMAIL_APP_PASSWORD:  ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL:     ${{ secrets.RECIPIENT_EMAIL }}
```

> ⭐ **GitHub Actions is completely free** for public repos and gives 2,000 minutes/month for private repos — more than enough for one daily job.

---

*Built with ❤️ — wishing your friend great success in her AI/ML job search in Germany! 🇩🇪*
