"""
Configuration settings for the job alert system.
"""
import os

# List of companies to monitor
# Just add the career page URL - the system will automatically discover and learn the API!
# 
# New Format (Automatic API Discovery):
# - name: Company name
# - slug: Unique identifier (lowercase with dashes). If using auto-discovery, this will be created automatically.
# - url: Career page URL
# - keywords: Job search keywords
# - locations: Location filters
# - use_api: If True (default), tries to use discovered API. If False, uses HTML scraping.
#
COMPANIES = [
    
]

# Legacy format (for backwards compatibility)
# Will be deprecated - please use COMPANIES above
COMPANY_URLS = []

# Email settings
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "vikram11102001@gmail.com")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Scraping settings
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
WAIT_FOR_CONTENT_TIMEOUT = 10000  # milliseconds
HEADLESS_MODE = True

# File paths
JOBS_DATA_FILE = "jobs_data/jobs_history.json"

# Job type filtering
# Only jobs matching these keywords (case-insensitive) will be included
JOB_TYPE_KEYWORDS = [
    "intern",
    "internship",
    "working student",
    "werkstudent",  # German for working student
    "part time",
    "part-time",
    "teilzeit",  # German for part-time
]

# Location filtering
# Only jobs in Germany will be included
LOCATION_KEYWORDS = [
    "germany",
    "deutschland",  # German for Germany
    "berlin",
    "munich",
    "münchen",
    "hamburg",
    "frankfurt",
    "cologne",
    "köln",
    "stuttgart",
    "düsseldorf",
    "dortmund",
    "essen",
    "leipzig",
    "bremen",
    "dresden",
    "hannover",
    "nuremberg",
    "nürnberg",
    "duisburg",
    "bochum",
    "wuppertal",
    "bonn",
    "bielefeld",
    "mannheim",
    "karlsruhe",
    "augsburg",
    "wiesbaden",
    "mönchengladbach",
    "gelsenkirchen",
    "aachen",
    "braunschweig",
    "kiel",
    "chemnitz",
    "halle",
    "magdeburg",
    "freiburg",
    "krefeld",
    "mainz",
    "lübeck",
    "erfurt",
    "oberhausen",
    "rostock",
    "kassel",
    "hagen",
    "potsdam",
    "saarbrücken",
    "hamm",
    "ludwigshafen",
    "mülheim",
    "oldenburg",
    "osnabrück",
    "leverkusen",
    "heidelberg",
    "solingen",
    "darmstadt",
    "regensburg",
    "ingolstadt",
    "würzburg",
    "fürth",
    "wolfsburg",
    "offenbach",
    "ulm",
    "heilbronn",
    "pforzheim",
    "göttingen",
    "bottrop",
    "recklinghausen",
    "remscheid",
    "bremerhaven",
    "jena",
    "trier",
    "erlangen",
]

# Generic selectors to try (in order of priority)
# The scraper will try these selectors if company-specific ones aren't provided
GENERIC_SELECTORS = {
    "job_containers": [
        "[class*='job'][class*='listing']",
        "[class*='job'][class*='item']",
        "[class*='position']",
        "[class*='career']",
        "article",
        ".job",
        ".position",
        "[role='listitem']",
    ],
    "title": [
        "[class*='title']",
        "[class*='job-name']",
        "h2",
        "h3",
        "a",
    ],
    "location": [
        "[class*='location']",
        "[class*='office']",
        "[class*='city']",
    ],
    "link": [
        "a[href*='job']",
        "a[href*='position']",
        "a[href*='career']",
        "a",
    ],
}
