"""
Main orchestration script for the job alert system.
Now with automatic API discovery!
"""
import sys
import re
import asyncio
from src.config import COMPANIES, COMPANY_URLS, JOBS_DATA_FILE, JOB_TYPE_KEYWORDS, JOB_FIELD_KEYWORDS, LOCATION_KEYWORDS
from src.dynamic_api_scraper import DynamicAPIScraper
from src.api_discovery import discover_company_api
from src.comparison import compare_and_update_jobs
from src.email_sender import send_email
from src.async_scraper import scrape_html_async  # Async HTML fallback


def slugify(name: str) -> str:
    """Convert company name to slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def filter_jobs_by_type_and_field(jobs, type_keywords=None, field_keywords=None):
    """Filter jobs by job type AND field keywords.
    
    Jobs must match:
    1. At least one job type keyword (intern, working student, etc.)
    2. At least one field keyword (AI, ML, Data Science, etc.)
    """
    if type_keywords is None:
        type_keywords = JOB_TYPE_KEYWORDS
    if field_keywords is None:
        field_keywords = JOB_FIELD_KEYWORDS
    
    filtered = []
    
    for job in jobs:
        title_lower = job['title'].lower()
        
        # Check if job matches type (intern/working student)
        matches_type = any(keyword.lower() in title_lower for keyword in type_keywords)
        
        # Check if job matches field (AI/ML/Data Science)
        matches_field = any(keyword.lower() in title_lower for keyword in field_keywords)
        
        # Job must match BOTH type AND field
        if matches_type and matches_field:
            filtered.append(job)
    
    return filtered


async def scrape_company_async(company, scraper):
    """Scrape a single company asynchronously."""
    name = company['name']
    slug = company.get('slug', slugify(name))
    url = company['url']
    keywords = company.get('keywords', ['intern', 'internship'])
    locations = company.get('locations', ['Germany'])
    use_api = company.get('use_api', True)
    
    print(f"\n{'='*60}")
    print(f"🏢 {name}")
    print(f"{'='*60}")
    
    jobs = []
    
    if use_api:
        # Try to use saved API configuration
        config = scraper.get_config(slug)
        
        if config:
            print(f"✅ Using saved API configuration")
            jobs = scraper.scrape_jobs(slug, keywords=keywords, location='DEU')
        else:
            # Auto-discover API on first run
            print(f"🔍 No saved API config found. Discovering API...")
            discovered_config = await discover_company_api(url)
            
            if discovered_config:
                print(f"✅ Successfully discovered API!")
                discovered_config['company_name'] = name
                scraper.save_config(slug, discovered_config)
                print(f"💾 Saved configuration for future use")
                
                # Try to scrape with discovered config
                jobs = scraper.scrape_jobs(slug, keywords=keywords, location='DEU')
            else:
                print(f"⚠️  Could not discover API. Falling back to HTML scraping...")
                use_api = False
    
    # Fallback to HTML scraping if API didn't work
    if not use_api or not jobs:
        if not use_api:
            print(f"📄 Using HTML scraping (API disabled)")
        else:
            print(f"📄 Falling back to HTML scraping")
        
        # Use async HTML scraper (we'll create this)
        try:
            html_jobs = await scrape_html_async(name, url, keywords, locations)
            jobs.extend(html_jobs)
        except Exception as e:
            print(f"❌ HTML scraping also failed: {str(e)}")
            jobs = []
    
    # Filter jobs by job type (location already filtered by API)
    if jobs:
        print(f"📊 Filtering {len(jobs)} jobs by job type and field...")
        filtered_jobs = filter_jobs_by_type_and_field(jobs, keywords)
        print(f"✅ {len(filtered_jobs)} jobs match criteria (internship/student + AI/ML/Data Science)")
        return filtered_jobs
    else:
        print(f"❌ No jobs found")
        return []


async def scrape_all_companies_async():
    """Scrape all companies using automatic API discovery."""
    scraper = DynamicAPIScraper()
    all_jobs = []
    
    # Use new COMPANIES config if available
    companies_to_scrape = COMPANIES if COMPANIES else COMPANY_URLS
    
    if not companies_to_scrape:
        print("⚠️  No companies configured!")
        return []
    
    for company in companies_to_scrape:
        jobs = await scrape_company_async(company, scraper)
        all_jobs.extend(jobs)
        
        # Be polite - wait between companies
        await asyncio.sleep(2)
    
    return all_jobs


def main():
    """
    Main entry point for job alert system.
    
    Workflow:
    1. Automatically discover and use APIs for all configured companies
    2. Fall back to HTML scraping if API discovery fails
    3. Compare results with historical data
    4. Send email if new jobs found
    """
    print("=" * 60)
    print("🚀 Job Alert System - Automatic API Discovery")
    print("=" * 60)
    
    # Step 1: Scrape all companies (with automatic API discovery)
    print("\n📊 Step 1: Fetching jobs...")
    current_jobs = asyncio.run(scrape_all_companies_async())
    
    print(f"\n{'='*60}")
    print(f"📈 Total jobs found: {len(current_jobs)}")
    print(f"{'='*60}")
    
    if not current_jobs:
        print("⚠️  No jobs found from any company. Please check your configuration.")
        return 0
    
    # Step 2: Compare with historical data and identify new jobs
    print("\n🔍 Step 2: Comparing with historical data...")
    new_jobs = compare_and_update_jobs(current_jobs, JOBS_DATA_FILE)
    
    if not new_jobs:
        print("✅ No new jobs found. Job history updated.")
        return 0
    
    print(f"🎯 Found {len(new_jobs)} new job(s)!")
    
    # Show new jobs
    print("\n📋 New Jobs:")
    for job in new_jobs:
        print(f"  • {job['title']} - {job['company']}")
        print(f"    📍 {job['location']}")
    
    # Step 3: Send email notification
    print("\n📧 Step 3: Sending email notification...")
    email_success = send_email(new_jobs)
    
    if email_success:
        print("\n" + "=" * 60)
        print("✅ Job Alert System completed successfully!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠️  Job Alert System completed with email errors")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
