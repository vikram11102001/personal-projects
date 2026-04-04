"""
Configuration for LinkedIn Job Agent.

Priority order for each setting:
  1. Environment variable  (use this on Render / Railway / GitHub Actions)
  2. Hardcoded value below (use this for local runs)

To run locally: edit the values in the CONFIG dict.
To deploy to cloud: set the corresponding environment variables and leave
the defaults unchanged.
"""

import os

CONFIG = {
    # ── Email Settings ─────────────────────────────────────────────────────────
    # Your Gmail address (the one that will SEND the email)
    "sender_email": os.environ.get("SENDER_EMAIL", "karthikeyavikram1101@gmail.com"),

    # Gmail App Password (NOT your Gmail login password!)
    # Generate at: https://myaccount.google.com/apppasswords
    # Steps: Google Account → Security → 2-Step Verification → App Passwords
    "gmail_app_password": os.environ.get("GMAIL_APP_PASSWORD", "bwmx bzct ekmi cicw"),

    # Email address where job digests will be delivered
    "recipient_email": os.environ.get("RECIPIENT_EMAIL", "vikram11102001@gmail.com"),

    # ── Schedule ───────────────────────────────────────────────────────────────
    # Time to send the daily email (24-hour format, local machine time)
    # For Germany morning: "08:00"
    "schedule_time": os.environ.get("SCHEDULE_TIME", "08:00"),

    # ── Search Settings ────────────────────────────────────────────────────────
    # How many "top trending" jobs to show when no new jobs are found
    "top_jobs_count": int(os.environ.get("TOP_JOBS_COUNT", "8")),

    # Max new jobs per email (to keep email readable)
    "max_new_jobs_per_email": int(os.environ.get("MAX_NEW_JOBS_PER_EMAIL", "20")),
}
