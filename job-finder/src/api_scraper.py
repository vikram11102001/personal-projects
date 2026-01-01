"""
API-based web scraper that directly calls job board APIs instead of parsing HTML.
This is more reliable and avoids bot detection.
"""
import requests
import time
from typing import List, Dict, Optional
from src.config import (
    JOB_TYPE_KEYWORDS,
    LOCATION_KEYWORDS
)


def scrape_mediamarkt_saturn_api(keywords: List[str] = None, country: str = "DEU") -> List[Dict]:
    """
    Scrape jobs directly from Media MarktSaturn's Azure Search API.
    
    Args:
        keywords: List of keywords to search for
        country: Country code (default: DEU for Germany)
        
    Returns:
        List of job dictionaries
    """
    api_url = "https://searchui.search.windows.net/indexes/mms-prod/docs/search"
    
    # Build the filter for the API request
    filters = []
    
    # Date filter (jobs posted before now)
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    filters.append(f"datePosted lt {now}")
    
    # Country filter
    filters.append(f"(addresses/any(jt: jt/country eq '{country}'))")
    
    filter_string = " and ".join(filters)
    filter_string += " and language eq 'en_US'"  # Add language filter
    
    # Build search query using regex pattern like the browser does
    if keywords:
        # Join keywords with OR in regex format
        search_text = "/.*(" + "|".join(keywords) + ").*/"
    else:
        search_text = "*"
    
    # API request payload (matching browser's format)
    payload = {
        "count": True,
        "facets": [],
        "filter": filter_string,
        "search": search_text,
        "queryType": "full",
        "searchFields": "jobId,title,description",
        "skip": 0,
        "top": 100  # Get up to 100 jobs
    }
    
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "api-key": "6BBD74F1CBD41E5B0232FB05C5B78ED9",  # Discovered from browser requests
        "referer": "https://careers.mediamarktsaturn.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        print(f"Calling MediaMarktSaturn API...")
        response = requests.post(
            f"{api_url}?api-version=2020-06-30",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"API returned status code: {response.status_code}")
            return []
        
        data = response.json()
        total_count = data.get("@odata.count", 0)
        jobs_data = data.get("value", [])
        
        print(f"API returned {len(jobs_data)} jobs (total: {total_count})")
        
        # Convert to our standard format
        jobs = []
        for job in jobs_data:
            # Extract location
            location = "Not specified"
            if job.get("addresses") and len(job["addresses"]) > 0:
                addr = job["addresses"][0]
                city = addr.get("city", "")
                country_code = addr.get("country", "")
                location = f"{city}, {country_code}" if city else country_code
            
            # Build job URL
            external_path = job.get("externalPath", "")
            job_url = f"https://careers.mediamarktsaturn.com{external_path}" if external_path else ""
            
            job_dict = {
                "company": "MediaMarkt Saturn",
                "title": job.get("title", ""),
                "location": location,
                "url": job_url,
                "employment_type": job.get("employmentType", ""),
                "career_level": job.get("careerLevel", ""),
                "date_posted": job.get("datePosted", ""),
            }
            
            jobs.append(job_dict)
        
        return jobs
        
    except Exception as e:
        print(f"Error calling MediaMarktSaturn API: {str(e)}")
        return []


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


def scrape_all_companies_api(company_configs: List[Dict]) -> List[Dict]:
    """
    Scrape jobs from all configured companies using their APIs.
    
    Args:
        company_configs: List of company configuration dictionaries
        
    Returns:
        List of all jobs from all companies
    """
    all_jobs = []
    
    for company in company_configs:
        company_name = company.get("name")
        
        if not company_name:
            continue
        
        # Check which company and call appropriate API
        if "mediamarkt" in company_name.lower() or "saturn" in company_name.lower():
            # Get keywords from config if specified
            keywords = company.get("keywords", ["intern", "internship", "werkstudent", "praktikum"])
            country = company.get("country", "DEU")
            
            jobs = scrape_mediamarkt_saturn_api(keywords=keywords, country=country)
            
            # Filter by job type and location
            filtered_jobs = []
            for job in jobs:
                # Check job type
                if not is_valid_job_type(job['title']):
                    continue
                
                # Check location
                if not is_valid_location(job['location']):
                    continue
                
                filtered_jobs.append(job)
            
            print(f"After filtering: {len(filtered_jobs)} jobs match criteria")
            all_jobs.extend(filtered_jobs)
        else:
            print(f"No API implementation for {company_name} yet")
        
        # Be polite - wait between companies
        time.sleep(1)
    
    return all_jobs
