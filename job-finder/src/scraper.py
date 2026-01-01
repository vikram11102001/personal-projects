"""
Web scraper module using Playwright to extract job postings from company career pages.
Uses BeautifulSoup for HTML parsing to avoid bot detection.
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config import (
    PAGE_LOAD_TIMEOUT,
    HEADLESS_MODE,
    JOB_TYPE_KEYWORDS,
    LOCATION_KEYWORDS
)


def scrape_jobs(company_name: str, url: str, custom_selectors: Optional[Dict] = None) -> List[Dict]:
    """
    Scrape job listings from a company's career page.
    
    Args:
        company_name: Name of the company
        url: URL of the careers page
        custom_selectors: Optional dict with custom selectors for this company
        
    Returns:
        List of job dictionaries with keys: company, title, location, url
    """
    jobs = []
    
    try:
        with sync_playwright() as p:
            # Launch browser with anti-bot detection measures
            browser = p.chromium.launch(
                headless=HEADLESS_MODE,
                args=['--disable-blink-features=AutomationControlled']
            )
            try:
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                # Hide webdriver property to avoid bot detection
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                print(f"Navigating to {company_name} careers page...")
                page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until='domcontentloaded')
                
                # Wait for dynamic content to load
                time.sleep(5)
                
                # Try to dismiss cookie banners
                try:
                    cookie_buttons = [
                        "button:has-text('Accept')",
                        "button:has-text('Accept all')",
                        "button:has-text('Agree')",
                        "[id*='accept']",
                        "[class*='accept']"
                    ]
                    for selector in cookie_buttons:
                        try:
                            if page.locator(selector).count() > 0:
                                page.locator(selector).first.click(timeout=2000)
                                time.sleep(1)
                                break
                        except:
                            continue
                except:
                    pass
                
                # Scroll to load lazy content
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                except:
                    pass
                
                # Get HTML content (safe - doesn't trigger bot detection)
                print(f"Getting page content for {company_name}...")
                html_content = page.content()
                print(f"Retrieved {len(html_content)} characters of HTML")
                
                # Parse HTML with BeautifulSoup
                print(f"Parsing jobs from HTML...")
                jobs = parse_jobs_from_html(html_content, company_name, url, custom_selectors)
                print(f"Found {len(jobs)} jobs from {company_name}")
                
            except PlaywrightTimeoutError:
                print(f"Timeout error while scraping {company_name} at {url}")
            except Exception as e:
                print(f"Error during scraping {company_name}: {str(e)}")
            finally:
                try:
                    browser.close()
                except:
                    pass
                    
    except Exception as e:
        print(f"Error launching browser for {company_name}: {str(e)}")
    
    return jobs


def parse_jobs_from_html(html_content: str, company_name: str, base_url: str, custom_selectors: Optional[Dict] = None) -> List[Dict]:
    """
    Parse job listings from HTML using BeautifulSoup.
    Avoids bot detection by not using Playwright DOM queries.
    """
    jobs = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Simple approach: find all links that might be job postings
    # Look for links containing job-related keywords
    all_links = soup.find_all('a', href=True)
    
    job_data_list = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Skip if empty
        if not text or not href:
            continue
        
        # Check if this looks like a job posting
        # (contains job-related paths or has substantial text)
        if ('job' in href.lower() or 'career' in href.lower() or 
            'position' in href.lower() or len(text) > 20):
            
            # Try to extract title and location from the link and surrounding context
            title = text
            location = "Not specified"
            
            # Look for location in parent or sibling elements
            parent = link.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                # Look for common location patterns
                for keyword in LOCATION_KEYWORDS:
                    if keyword.lower() in parent_text.lower():
                        location = parent_text
                        break
            
            # Build absolute URL
            if href.startswith('http'):
                job_url = href
            elif href.startswith('/'):
                parsed = urlparse(base_url)
                job_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                job_url = f"{base_url.rstrip('/')}/{href.lstrip('/')}"
            
            job_data_list.append({
                "company": company_name,
                "title": title,
                "location": location,
                "url": job_url
            })
    
    # Filter jobs by type and location
    for job in job_data_list:
        # Check job type
        if not is_valid_job_type(job['title']):
            continue
        
        # Check location (if pre-filtered URL, might already be Germany)
        # But still apply filter to be safe
        if job['location'] != "Not specified" and not is_valid_location(job['location']):
            continue
        
        jobs.append(job)
    
    return jobs


def is_valid_job_type(job_title: str) -> bool:
    """Check if job title matches allowed job types."""
    if not job_title:
        return False
    
    title_lower = job_title.lower()
    for keyword in JOB_TYPE_KEYWORDS:
        if keyword.lower() in title_lower:
            return True
    
    return False


def is_valid_location(location: str) -> bool:
    """Check if location is in Germany."""
    if not location:
        return False
    
    location_lower = location.lower()
    for keyword in LOCATION_KEYWORDS:
        if keyword.lower() in location_lower:
            return True
    
    return False


def scrape_all_companies(company_configs: List[Dict]) -> List[Dict]:
    """
    Scrape jobs from all configured companies.
    
    Args:
        company_configs: List of company configuration dictionaries
        
    Returns:
        List of all jobs from all companies
    """
    all_jobs = []
    
    for company in company_configs:
        company_name = company.get("name")
        url = company.get("url")
        
        if not company_name or not url:
            print(f"Skipping invalid company config: {company}")
            continue
        
        # Extract custom selectors if provided
        custom_selectors = {}
        for key in ["job_container", "title_selector", "location_selector", "link_selector"]:
            if key in company:
                custom_selectors[key] = company[key]
        
        jobs = scrape_jobs(company_name, url, custom_selectors if custom_selectors else None)
        all_jobs.extend(jobs)
        
        # Be polite - wait between companies
        time.sleep(2)
    
    return all_jobs
