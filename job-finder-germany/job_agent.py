"""
LinkedIn AI/ML Job Agent for Germany
Scrapes LinkedIn jobs daily and sends email digest.
No paid APIs required — uses free tools only.
"""

import os
import sys
import argparse
import sqlite3
import smtplib
import schedule
import time
import logging
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
from config import CONFIG

# ── Ensure logs directory exists ───────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ── Database ───────────────────────────────────────────────────────────────────
def init_db(db_path: str = "jobs.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            job_type    TEXT,
            url         TEXT,
            date_found  TEXT,
            sent        INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_digests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_at     TEXT,
            new_count   INTEGER,
            top_count   INTEGER
        )
    """)
    conn.commit()
    conn.close()


def get_conn(db_path: str = "jobs.db"):
    return sqlite3.connect(db_path)


def save_jobs(jobs: list, db_path: str = "jobs.db") -> list:
    """Saves jobs to DB, returns only the newly added ones."""
    conn = get_conn(db_path)
    new_jobs = []
    for job in jobs:
        try:
            conn.execute(
                "INSERT INTO jobs (id, title, company, location, job_type, url, date_found) VALUES (?,?,?,?,?,?,?)",
                (job["id"], job["title"], job["company"], job["location"],
                 job["job_type"], job["url"], datetime.now().isoformat())
            )
            new_jobs.append(job)
        except sqlite3.IntegrityError:
            pass  # Already exists
    conn.commit()
    conn.close()
    log.info(f"Saved {len(new_jobs)} new jobs out of {len(jobs)} fetched.")
    return new_jobs


def get_top_jobs(limit: int = 5, db_path: str = "jobs.db") -> list:
    """Returns top previously sent jobs (trending / popular companies)."""
    conn = get_conn(db_path)
    rows = conn.execute("""
        SELECT title, company, location, job_type, url
        FROM jobs
        WHERE sent = 1
        ORDER BY date_found DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"title": r[0], "company": r[1], "location": r[2],
         "job_type": r[3], "url": r[4]}
        for r in rows
    ]


def mark_sent(job_ids: list, db_path: str = "jobs.db"):
    conn = get_conn(db_path)
    conn.executemany(
        "UPDATE jobs SET sent = 1 WHERE id = ?",
        [(jid,) for jid in job_ids]
    )
    conn.commit()
    conn.close()


def log_digest(new_count: int, top_count: int, db_path: str = "jobs.db"):
    conn = get_conn(db_path)
    conn.execute(
        "INSERT INTO sent_digests (sent_at, new_count, top_count) VALUES (?,?,?)",
        (datetime.now().isoformat(), new_count, top_count)
    )
    conn.commit()
    conn.close()


# ── LinkedIn Scraper ───────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JOB_TYPES = {
    "internship": "I",
    "part_time":  "P",
    "workstudie": "P",   # LinkedIn lumps part-time
}

SEARCH_QUERIES = [
    # ── Internships ────────────────────────────────────────────────────────────
    ("Artificial Intelligence Engineer Intern Germany",     "Internship"),
    ("Machine Learning Engineer Intern Germany",            "Internship"),
    ("Data Science Intern Germany",                         "Internship"),
    ("Data Analyst Intern Germany",                         "Internship"),
    ("AI Software Developer Intern Germany",                "Internship"),
    ("MLOps Engineer Intern Germany",                       "Internship"),
    ("Computer Vision Engineer Intern Germany",             "Internship"),
    ("NLP Engineer Intern Germany",                         "Internship"),
    # ── Werkstudent (Working Student) ──────────────────────────────────────────
    ("Machine Learning Werkstudent Germany",                "Working Student"),
    ("Data Science Werkstudent Germany",                    "Working Student"),
    ("Data Analyst Werkstudent Germany",                    "Working Student"),
    ("AI Engineer Werkstudent Germany",                     "Working Student"),
    # ── Part-time ─────────────────────────────────────────────────────────────
    ("Machine Learning Engineer Part Time Germany",         "Part-time"),
    ("Data Analyst Part Time Germany",                      "Part-time"),
    ("Artificial Intelligence Developer Part Time Germany", "Part-time"),
]


def scrape_linkedin(query: str, job_type_label: str) -> list:
    """
    Scrape LinkedIn public job search (no login required).
    LinkedIn's public /jobs/search endpoint works without authentication.
    """
    jobs = []
    # LinkedIn public jobs URL
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords":     query,
        "location":     "Germany",
        "f_TPR":        "r86400",    # Past 24 hours
        "f_JT":         "I,P",       # Internship & Part-time
        "start":        0,
        "count":        25,
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("li")

        for card in cards:
            try:
                job_id_tag = card.find("div", {"data-entity-urn": True})
                if not job_id_tag:
                    base = card.find("a", href=True)
                    if not base:
                        continue
                    href = base["href"]
                    job_id = href.split("/view/")[-1].split("/")[0].split("?")[0]
                else:
                    urn = job_id_tag["data-entity-urn"]
                    job_id = urn.split(":")[-1]

                title_tag   = card.find("h3") or card.find("span", {"class": lambda c: c and "title" in c.lower()})
                company_tag = card.find("h4") or card.find("a", {"data-tracking-control-name": "public_jobs_jserp-name"})
                location_tag = card.find("span", {"class": lambda c: c and "location" in c.lower()})
                link_tag    = card.find("a", href=True)

                title   = title_tag.get_text(strip=True)   if title_tag   else "N/A"
                company = company_tag.get_text(strip=True) if company_tag else "N/A"
                location = location_tag.get_text(strip=True) if location_tag else "Germany"
                link    = link_tag["href"].split("?")[0]   if link_tag    else "#"

                if title == "N/A" or not job_id:
                    continue

                # Deduplicate by job_id
                jobs.append({
                    "id":       job_id,
                    "title":    title,
                    "company":  company,
                    "location": location,
                    "job_type": job_type_label,
                    "url":      link,
                })
            except Exception as e:
                log.debug(f"Card parse error: {e}")
                continue

    except requests.exceptions.RequestException as e:
        log.warning(f"Request failed for '{query}': {e}")

    return jobs


def scrape_linkedin_alternative(query: str, job_type_label: str) -> list:
    """
    Alternative scraper using LinkedIn's standard job search page.
    Falls back if the API endpoint is blocked.
    """
    jobs = []
    url = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": query,
        "location": "Germany",
        "f_TPR":    "r86400",
        "f_JT":     "I,P",
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.find_all("div", {"class": lambda c: c and "job-search-card" in (c or "")})
        if not cards:
            cards = soup.find_all("li", {"class": lambda c: c and "result-card" in (c or "")})

        for card in cards:
            try:
                link_tag    = card.find("a", href=True)
                title_tag   = card.find("h3")
                company_tag = card.find("h4")
                location_tag = card.find("span", {"class": lambda c: c and "location" in (c or "").lower()})

                if not link_tag or not title_tag:
                    continue

                href    = link_tag["href"]
                job_id  = href.split("/view/")[-1].split("/")[0].split("?")[0]
                title   = title_tag.get_text(strip=True)
                company = company_tag.get_text(strip=True) if company_tag else "N/A"
                location = location_tag.get_text(strip=True) if location_tag else "Germany"

                jobs.append({
                    "id":       job_id,
                    "title":    title,
                    "company":  company,
                    "location": location,
                    "job_type": job_type_label,
                    "url":      href.split("?")[0],
                })
            except Exception:
                continue

    except requests.exceptions.RequestException as e:
        log.warning(f"Alternative scraper failed for '{query}': {e}")

    return jobs


def fetch_all_jobs() -> list:
    """Run all search queries and deduplicate by job ID."""
    all_jobs = {}
    for query, label in SEARCH_QUERIES:
        log.info(f"Scraping: '{query}'")
        jobs = scrape_linkedin(query, label)
        if not jobs:
            log.info(f"  → No results via API endpoint, trying alternative...")
            jobs = scrape_linkedin_alternative(query, label)
        log.info(f"  → Found {len(jobs)} jobs")
        for job in jobs:
            all_jobs[job["id"]] = job
        time.sleep(random.uniform(2, 4))  # Polite delay

    return list(all_jobs.values())


# ── Email Builder ──────────────────────────────────────────────────────────────
def build_email_html(new_jobs: list, top_jobs: list) -> str:
    """Build a beautiful HTML email."""
    today = datetime.now().strftime("%A, %d %B %Y")
    has_new = len(new_jobs) > 0

    def job_card(job: dict, badge_color: str = "#0077B5") -> str:
        jtype_colors = {
            "Internship":      "#7C3AED",
            "Working Student": "#059669",
            "Part-time":       "#D97706",
        }
        badge_bg = jtype_colors.get(job.get("job_type", ""), "#0077B5")
        return f"""
        <tr>
          <td style="padding:12px 0; border-bottom:1px solid #f0f0f0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <a href="{job['url']}" style="font-size:16px; font-weight:700; color:#0077B5; text-decoration:none;">
                    {job['title']}
                  </a>
                  <br>
                  <span style="font-size:14px; color:#333; font-weight:600;">🏢 {job['company']}</span>
                  &nbsp;&nbsp;
                  <span style="font-size:13px; color:#666;">📍 {job['location']}</span>
                  <br>
                  <span style="display:inline-block; margin-top:6px; padding:3px 10px; background:{badge_bg}; color:#fff; border-radius:12px; font-size:11px; font-weight:600;">
                    {job.get('job_type', 'Job')}
                  </span>
                </td>
                <td align="right" valign="middle" style="min-width:90px;">
                  <a href="{job['url']}" style="display:inline-block; padding:8px 16px; background:#0077B5; color:#fff; border-radius:6px; text-decoration:none; font-size:13px; font-weight:600;">
                    Apply →
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    new_jobs_html = "".join(job_card(j) for j in new_jobs) if has_new else ""
    top_jobs_html = "".join(job_card(j) for j in top_jobs)

    new_section = f"""
    <tr>
      <td style="padding:24px 32px 0;">
        <h2 style="margin:0 0 6px; font-size:20px; color:#111; font-family:Georgia,serif;">
          🆕 {len(new_jobs)} New Job{'s' if len(new_jobs)!=1 else ''} Found Today
        </h2>
        <p style="margin:0 0 16px; color:#666; font-size:14px;">
          Fresh listings matching your AI/ML/Data search in Germany
        </p>
        <table width="100%" cellpadding="0" cellspacing="0">
          {new_jobs_html}
        </table>
      </td>
    </tr>
    """ if has_new else f"""
    <tr>
      <td style="padding:24px 32px 0;">
        <div style="background:#FFF7ED; border-left:4px solid #F97316; border-radius:0 8px 8px 0; padding:16px 20px;">
          <p style="margin:0; font-size:15px; color:#92400E; font-weight:600;">
            😴 No new AI/ML jobs found in Germany today
          </p>
          <p style="margin:6px 0 0; font-size:13px; color:#B45309;">
            Check back tomorrow — the market moves fast!
          </p>
        </div>
      </td>
    </tr>
    """

    trending_section = f"""
    <tr>
      <td style="padding:24px 32px 0;">
        <h2 style="margin:0 0 6px; font-size:20px; color:#111; font-family:Georgia,serif;">
          🔥 Trending Companies Right Now
        </h2>
        <p style="margin:0 0 16px; color:#666; font-size:14px;">
          Top picks from recent listings — these companies are hiring actively
        </p>
        <table width="100%" cellpadding="0" cellspacing="0">
          {top_jobs_html}
        </table>
      </td>
    </tr>
    """ if top_jobs else ""

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0; padding:0; background:#F4F6F9; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F9; padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0077B5 0%,#00A0DC 100%); padding:32px; text-align:center;">
              <p style="margin:0 0 4px; font-size:12px; color:rgba(255,255,255,0.7); letter-spacing:2px; text-transform:uppercase;">Daily Job Digest</p>
              <h1 style="margin:0; font-size:28px; color:#fff; font-family:Georgia,serif; font-weight:700;">
                🤖 AI, ML &amp; Data Jobs in Germany
              </h1>
              <p style="margin:8px 0 0; color:rgba(255,255,255,0.85); font-size:14px;">{today}</p>
            </td>
          </tr>

          <!-- Stats Bar -->
          <tr>
            <td style="background:#F0F9FF; padding:16px 32px; border-bottom:1px solid #E0F2FE;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <span style="font-size:24px; font-weight:800; color:#0077B5;">{len(new_jobs)}</span>
                    <br><span style="font-size:11px; color:#666; text-transform:uppercase; letter-spacing:1px;">New Today</span>
                  </td>
                  <td align="center" style="border-left:1px solid #BAE6FD; border-right:1px solid #BAE6FD;">
                    <span style="font-size:24px; font-weight:800; color:#059669;">Intern/Part-time</span>
                    <br><span style="font-size:11px; color:#666; text-transform:uppercase; letter-spacing:1px;">Job Types</span>
                  </td>
                  <td align="center">
                    <span style="font-size:24px; font-weight:800; color:#7C3AED;">🇩🇪</span>
                    <br><span style="font-size:11px; color:#666; text-transform:uppercase; letter-spacing:1px;">Germany</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- New Jobs Section -->
          {new_section}

          <!-- Divider -->
          <tr><td style="padding:20px 32px 0;"><hr style="border:none; border-top:2px dashed #E5E7EB;"></td></tr>

          <!-- Trending Section -->
          {trending_section}

          <!-- Footer -->
          <tr>
            <td style="padding:24px 32px; background:#F9FAFB; border-top:1px solid #E5E7EB; text-align:center;">
              <p style="margin:0 0 8px; font-size:13px; color:#666;">
                🔍 Searches run daily at <strong>{CONFIG.get('schedule_time','08:00')}</strong> (your time zone)
              </p>
              <p style="margin:0; font-size:12px; color:#999;">
                Powered by LinkedIn Job Agent · Built with ❤️ for your friend in Germany
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
"""


def build_plain_text(new_jobs: list, top_jobs: list) -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    lines = [f"AI / ML / Data Job Digest — {today}", "=" * 50]

    if new_jobs:
        lines.append(f"\n🆕 {len(new_jobs)} NEW JOBS FOUND TODAY\n")
        for j in new_jobs:
            lines.append(f"• {j['title']} @ {j['company']}")
            lines.append(f"  📍 {j['location']}  |  🏷 {j['job_type']}")
            lines.append(f"  🔗 {j['url']}\n")
    else:
        lines.append("\n😴 No new AI/ML jobs found today.\n")

    if top_jobs:
        lines.append("\n🔥 TRENDING COMPANIES\n")
        for j in top_jobs:
            lines.append(f"• {j['title']} @ {j['company']}")
            lines.append(f"  📍 {j['location']}  |  🏷 {j['job_type']}")
            lines.append(f"  🔗 {j['url']}\n")

    return "\n".join(lines)


# ── Email Sender ───────────────────────────────────────────────────────────────
def send_email(new_jobs: list, top_jobs: list):
    cfg = CONFIG
    subject_prefix = f"🤖 [{len(new_jobs)} New]" if new_jobs else "😴 [No New Jobs]"
    subject = f"{subject_prefix} AI/ML/Data Jobs in Germany — {datetime.now().strftime('%d %b %Y')}"

    # Support comma-separated list of recipients; strip any stray newlines/spaces
    raw_recipients = cfg["recipient_email"].replace("\n", "").replace("\r", "")
    recipients = [r.strip() for r in raw_recipients.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Job Agent <{cfg['sender_email']}>"
    msg["To"]      = ", ".join(recipients)  # single-line, no folding issues

    msg.attach(MIMEText(build_plain_text(new_jobs, top_jobs), "plain"))
    msg.attach(MIMEText(build_email_html(new_jobs, top_jobs),  "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(cfg["sender_email"], cfg["gmail_app_password"])
            server.sendmail(cfg["sender_email"], recipients, msg.as_string())
        log.info(f"✅ Email sent to {recipients} | new={len(new_jobs)} top={len(top_jobs)}")
        return True
    except Exception as e:
        log.error(f"❌ Email failed: {e}")
        return False


# ── Main Job ───────────────────────────────────────────────────────────────────
def run_daily_job():
    log.info("=" * 60)
    log.info("🚀 Starting daily LinkedIn job scrape...")
    log.info("=" * 60)

    # 1. Scrape LinkedIn
    fetched = fetch_all_jobs()
    log.info(f"Total unique jobs fetched: {len(fetched)}")

    # 2. Save and get new ones
    new_jobs = save_jobs(fetched)

    # 3. Get top trending jobs from history (if no new ones, pull more)
    limit = 5 if new_jobs else 8
    top_jobs = get_top_jobs(limit=limit)

    # 4. Send email
    success = send_email(new_jobs, top_jobs)

    # 5. Mark new jobs as sent
    if success and new_jobs:
        mark_sent([j["id"] for j in new_jobs])

    # 6. Log the digest
    log_digest(len(new_jobs), len(top_jobs))

    log.info("✅ Daily job complete.\n")


# ── Scheduler ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn AI/ML Job Agent for Germany")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run one scrape + email immediately, then exit (use this for GitHub Actions / cron)",
    )
    args = parser.parse_args()

    init_db()

    if args.run_once:
        log.info("▶️  --run-once mode: running single job then exiting.")
        run_daily_job()
        sys.exit(0)

    log.info(f"⏰ Scheduling daily job at {CONFIG['schedule_time']}...")
    log.info(f"📧 Will send to: {CONFIG['recipient_email']}")  # comma-separated list supported

    schedule.every().day.at(CONFIG["schedule_time"]).do(run_daily_job)

    # Run immediately on first launch
    log.info("▶️  Running first job immediately...")
    run_daily_job()

    log.info("⏳ Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)
