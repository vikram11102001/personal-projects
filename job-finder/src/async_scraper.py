"""
Async HTML scraper for fallback when API discovery fails.
This is compatible with the async main script.
"""
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config import PAGE_LOAD_TIMEOUT, HEADLESS_MODE


async def scrape_html_async(
    company_name: str,
    url: str,
    keywords: List[str],
    locations: List[str]
) -> List[Dict]:
    """
    Async HTML scraper for when API discovery fails.
    
    Args:
        company_name: Name of the company
        url: Career page URL
        keywords: Job type keywords to filter
        locations: Location keywords to filter
        
    Returns:
        List of job dictionaries
    """
    jobs = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=HEADLESS_MODE,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Hide webdriver property
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                print(f"📄 Loading page with HTML parser...")
                await page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until='domcontentloaded')
                
                # Wait for content
                await asyncio.sleep(5)
                
                # Try to dismiss cookie banners
                try:
                    cookie_buttons = [
                        "button:has-text('Accept')",
                        "button:has-text('Accept all')",
                        "button:has-text('Agree')",
                    ]
                    for selector in cookie_buttons:
                        try:
                            count = await page.locator(selector).count()
                            if count > 0:
                                await page.locator(selector).first.click(timeout=2000)
                                await asyncio.sleep(1)
                                break
                        except:
                            continue
                except:
                    pass
                
                # Scroll to load lazy content
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                except:
                    pass
                
                # Get HTML content
                html_content = await page.content()
                print(f"📊 Retrieved {len(html_content)} characters of HTML")
                
                # Parse HTML
                jobs = parse_jobs_from_html_async(
                    html_content, company_name, url, keywords, locations
                )
                print(f"✅ Found {len(jobs)} jobs via HTML scraping")
                
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ HTML scraping error: {str(e)}")
    
    return jobs


def parse_jobs_from_html_async(
    html_content: str,
    company_name: str,
    base_url: str,
    keywords: List[str],
    locations: List[str]
) -> List[Dict]:
    """Parse jobs from HTML content."""
    jobs = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all links
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        if not text or not href:
            continue
        
        # Check if this looks like a job posting
        if ('job' in href.lower() or 'career' in href.lower() or 
            'position' in href.lower() or len(text) > 20):
            
            title = text
            location = "Not specified"
            
            # Look for location in parent elements
            parent = link.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                for loc_keyword in locations:
                    if loc_keyword.lower() in parent_text.lower():
                        # Extract the relevant location part
                        location = parent_text[:100]  # Limit length
                        break
            
            # Build absolute URL
            if href.startswith('http'):
                job_url = href
            elif href.startswith('/'):
                parsed = urlparse(base_url)
                job_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                job_url = f"{base_url.rstrip('/')}/{href.lstrip('/')}"
            
            # Check if title matches keywords
            title_lower = title.lower()
            if any(keyword.lower() in title_lower for keyword in keywords):
                jobs.append({
                    "company": company_name,
                    "title": title,
                    "location": location,
                    "url": job_url
                })
    
    return jobs
