"""
Email notification module using Gmail SMTP.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from src.config import SMTP_SERVER, SMTP_PORT, GMAIL_EMAIL, GMAIL_APP_PASSWORD, EMAIL_RECIPIENT


def format_job_email(jobs: List[Dict]) -> str:
    """
    Format job list into HTML email content.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        HTML formatted email body
    """
    if not jobs:
        return ""
    
    html_content = """
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .job-item {{
                margin-bottom: 25px;
                padding: 15px;
                border-left: 4px solid #4CAF50;
                background-color: #f9f9f9;
            }}
            .company {{
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 5px;
            }}
            .title {{
                font-size: 16px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .location {{
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }}
            .link {{
                font-size: 14px;
            }}
            .link a {{
                color: #4CAF50;
                text-decoration: none;
                font-weight: bold;
            }}
            .link a:hover {{
                text-decoration: underline;
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 24px;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #ddd;
                font-size: 12px;
                color: #999;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            🎯 New Job Alerts
        </div>
        <div style="padding: 20px;">
            <p>Found <strong>{count}</strong> new job {posting}:</p>
    """.format(count=len(jobs), posting="posting" if len(jobs) == 1 else "postings")
    
    for job in jobs:
        html_content += f"""
            <div class="job-item">
                <div class="company">{job.get('company', 'Unknown Company')}</div>
                <div class="title">{job.get('title', 'Unknown Title')}</div>
                <div class="location">📍 {job.get('location', 'Unknown Location')}</div>
                <div class="link">🔗 <a href="{job.get('url', '#')}">View Job Posting</a></div>
            </div>
        """
    
    html_content += """
        </div>
        <div class="footer">
            This is an automated message from your Job Alert System
        </div>
    </body>
    </html>
    """
    
    return html_content


def send_email(jobs: List[Dict], recipient_email: str = None) -> bool:
    """
    Send email notification with new job listings.
    
    Args:
        jobs: List of new job dictionaries
        recipient_email: Email address to send to (defaults to config value)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not jobs:
        print("No new jobs to send. Skipping email notification.")
        return True
    
    recipient = recipient_email or EMAIL_RECIPIENT
    
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        print("ERROR: Gmail credentials not configured. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables.")
        return False
    
    if not recipient:
        print("ERROR: No recipient email configured. Please set EMAIL_RECIPIENT.")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🎯 New Job Alerts - {len(jobs)} {'position' if len(jobs) == 1 else 'positions'} found"
        message["From"] = GMAIL_EMAIL
        message["To"] = recipient
        
        # Create HTML content
        html_body = format_job_email(jobs)
        
        # Create plain text version as fallback
        text_body = f"New Jobs Found ({len(jobs)} positions):\n\n"
        for job in jobs:
            text_body += f"Company: {job.get('company', 'Unknown')}\n"
            text_body += f"Title: {job.get('title', 'Unknown')}\n"
            text_body += f"Location: {job.get('location', 'Unknown')}\n"
            text_body += f"Link: {job.get('url', 'N/A')}\n"
            text_body += "\n" + "-" * 50 + "\n\n"
        
        # Attach both versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Connect to Gmail SMTP server
        print(f"Connecting to Gmail SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Email sent successfully to {recipient} with {len(jobs)} job(s)")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ ERROR: Gmail authentication failed. Please check your email and app password.")
        return False
    except Exception as e:
        print(f"❌ ERROR sending email: {str(e)}")
        return False
