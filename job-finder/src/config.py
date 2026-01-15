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
    {
        "name": "MediaMarkt Saturn",
        "slug": "mediamarkt-saturn",  # This slug matches the config in api_configs.json
        "url": "https://careers.mediamarktsaturn.com/",
        "keywords": ["intern", "internship", "werkstudent", "working student"],
        "locations": ["Germany", "DEU"],
        "use_api": True,  # Use automatic API discovery
    },
    {
        "name": "Robominds",
        "url": "https://join.com/companies/robominds",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany", "Munich"],
    },
    
    # Only keeping reliably working companies for now
    # MediaMarkt Saturn works perfectly with API
    
    # Companies with intermittent issues (browser detection):
    # You can try adding these back, but they may fail sometimes
    {
        "name": "Celonis",
        "url": "https://careers.celonis.com/join-us/open-positions?seniority=Working+Student+%26+Intern&groupedLocation=Munich%2C+Germany%7CRemote%2C+Germany",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany", "Munich", "Remote"],
        "use_api": False,  # Disable API - HTML scraping works better for pre-filtered URLs
    },

    {
        "name": "AirBus",
        "url": "https://ag.wd3.myworkdayjobs.com/en-US/Airbus?locationCountry=dcc5b7608d8644b3a93716604e78e995&workerSubType=f5811cef9cb50193723ed01d470a6e15",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany", "Munich", "Remote"],
        "use_api": False,  # Disable API - HTML scraping works better for pre-filtered URLs
    },

    # New companies added 2026-01-15
    {
        "name": "Infineon",
        "url": "https://jobs.infineon.com/careers?domain=infineon.com&start=0&location=Germany&pid=563808968063175&sort_by=match&filter_include_remote=0",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Siemens",
        "slug": "siemens",  # API config already exists in api_configs.json
        "url": "https://jobs.siemens.com/en_US/externaljobs?ste_sid=5f855cdd733bcdc8f16bf56668a0c81b",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany"],
        "use_api": True,  # Will use existing API config
    },
    {
        "name": "BSH Group",
        "url": "https://jobs.bsh-group.de/index",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Vinolinde",
        "url": "https://join.com/companies/vinolinde",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Stability AI",
        "url": "https://stability.ai/careers",
        "keywords": ["intern", "internship", "working student"],
        "locations": ["Germany", "Remote"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Trusteq",
        "url": "https://trusteq-gmbh.jobs.personio.de/?language=de",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Capgemini",
        "url": "https://www.capgemini.com/de-de/karriere/",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student", "praktikum"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Avelios",
        "url": "https://www.avelios.com/careers",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student"],
        "locations": ["Germany", "Munich", "Bavaria"],
        "use_api": True,  # Try API discovery first
    },
    {
        "name": "Valeo",
        "url": "https://www.valeo.com/en/career-in-germany/",
        "keywords": ["intern", "internship", "werkstudent", "working student", "student", "praktikant"],
        "locations": ["Germany"],
        "use_api": True,  # Try API discovery first
    },
    
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

# Job field filtering
# Only jobs matching these field keywords (case-insensitive) will be included
# Jobs must match BOTH job type AND field keywords
JOB_FIELD_KEYWORDS = [
    # Artificial Intelligence
    "artificial intelligence",
    "ai",
    "machine learning",
    "ml",
    "deep learning",
    "neural network",
    "computer vision",
    "cv",
    "natural language processing",
    "nlp",
    "large language model",
    "llm",
    "gen ai",
    "generative ai",
    
    # Data Science
    "data science",
    "data scientist",
    "data analytics",
    "data analyst",
    "data engineer",
    "data engineering",
    
    # Related fields
    "machine intelligence",
    "intelligent systems",
    "autonomous systems",
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
