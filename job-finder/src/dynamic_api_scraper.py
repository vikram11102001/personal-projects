"""
Dynamic API Scraper

Uses discovered API configurations to scrape jobs from any company
without writing custom scraper code for each one.
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class DynamicAPIScraper:
    """Scrapes jobs using dynamically discovered API configurations."""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                'api_configs.json'
            )
        self.config_file = config_file
        self.configs = self._load_configs()
    
    def _load_configs(self) -> Dict:
        """Load all API configurations."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_configs(self):
        """Save configurations back to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.configs, f, indent=2)
    
    def save_config(self, company_slug: str, config: Dict):
        """Save a new API configuration."""
        config['last_verified'] = datetime.utcnow().isoformat() + 'Z'
        config['status'] = 'active'
        self.configs[company_slug] = config
        self._save_configs()
    
    def get_config(self, company_slug: str) -> Optional[Dict]:
        """Get API configuration for a company."""
        return self.configs.get(company_slug)
    
    def scrape_jobs(
        self,
        company_slug: str,
        keywords: List[str] = None,
        location: str = "DEU",
        max_results: int = 100
    ) -> List[Dict]:
        """
        Scrape jobs using a saved API configuration.
        
        Args:
            company_slug: Company identifier (e.g., 'mediamarkt-saturn')
            keywords: Search keywords
            location: Location filter
            max_results: Maximum number of results
            
        Returns:
            List of standardized job dictionaries
        """
        config = self.get_config(company_slug)
        
        if not config:
            print(f"❌ No API configuration found for '{company_slug}'")
            return []
        
        print(f"📡 Calling {config.get('company_name', company_slug)} API...")
        
        try:
            # Prepare the request
            endpoint = config['endpoint']
            method = config['method']
            headers = config.get('headers', {})
            payload_template = config.get('payload_template', {})
            
            # Replace template variables
            payload = self._prepare_payload(
                payload_template,
                keywords=keywords,
                location=location,
                max_results=max_results
            )
            
            # Make the request
            if method == 'POST':
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
            else:  # GET
                response = requests.get(
                    endpoint,
                    params=payload,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code != 200:
                print(f"❌ API returned status {response.status_code}")
                return []
            
            # Parse the response
            data = response.json()
            jobs = self._parse_response(data, config)
            
            print(f"✅ Found {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            print(f"❌ Error calling API: {str(e)}")
            return []
    
    def _prepare_payload(
        self,
        template: Dict,
        keywords: List[str] = None,
        location: str = "DEU",
        max_results: int = 100
    ) -> Dict:
        """Prepare API payload from template by replacing variables."""
        if not template:
            return {}
        
        # Convert template to string for replacement
        template_str = json.dumps(template)
        
        # Replace common variables
        replacements = {
            '{keywords}': '|'.join(keywords) if keywords else 'intern|internship',
            '{country}': location,
            '{location}': location,
            '{max_results}': str(max_results),
            '{current_time}': datetime.utcnow().isoformat() + 'Z'
        }
        
        for key, value in replacements.items():
            template_str = template_str.replace(key, value)
        
        # Parse back to dict
        try:
            return json.loads(template_str)
        except:
            return template
    
    def _parse_response(self, data: Dict, config: Dict) -> List[Dict]:
        """
        Parse API response to extract jobs.
        
        Uses response_format from config if available, otherwise tries
        to intelligently detect the job array and fields.
        """
        jobs = []
        
        # Try to get response format from config
        response_format = config.get('response_format', {})
        
        # Extract the jobs array
        jobs_data = self._extract_jobs_array(data, response_format)
        
        if not jobs_data:
            print("⚠️  Could not find jobs array in response")
            return []
        
        company_name = config.get('company_name', 'Unknown')
        
        # Parse each job
        for job_data in jobs_data:
            job = self._parse_job_item(job_data, company_name, response_format)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _extract_jobs_array(self, data: Dict, response_format: Dict) -> List:
        """Extract the array of jobs from response."""
        # Try configured path first
        jobs_path = response_format.get('jobs_path')
        if jobs_path and jobs_path in data:
            return data[jobs_path]
        
        # Try common paths
        common_paths = ['value', 'data', 'results', 'jobs', 'items', 'records']
        for path in common_paths:
            if path in data:
                value = data[path]
                if isinstance(value, list):
                    return value
        
        # If data itself is a list
        if isinstance(data, list):
            return data
        
        return []
    
    def _parse_job_item(
        self,
        job_data: Dict,
        company_name: str,
        response_format: Dict
    ) -> Optional[Dict]:
        """Parse a single job item from the response."""
        try:
            # Extract fields using config or intelligent detection
            title = self._extract_field(
                job_data,
                response_format.get('title_field'),
                ['title', 'jobTitle', 'position', 'name']
            )
            
            location = self._extract_field(
                job_data,
                response_format.get('location_fields'),
                ['location', 'city', 'address', 'place']
            )
            
            # Handle nested location (like MediaMarkt's addresses array)
            if isinstance(location, list) and len(location) > 0:
                addr = location[0]
                if isinstance(addr, dict):
                    city = addr.get('city', '')
                    country = addr.get('country', '')
                    location = f"{city}, {country}" if city else country
            
            url = self._extract_field(
                job_data,
                response_format.get('url_field'),
                ['url', 'link', 'href', 'externalPath', 'jobUrl']
            )
            
            # Add URL prefix if configured
            if url and response_format.get('url_prefix'):
                if not url.startswith('http'):
                    url = response_format['url_prefix'] + url
            
            # Create standardized job object
            job = {
                'company': company_name,
                'title': title or 'Unknown',
                'location': location or 'Not specified',
                'url': url or '',
                'employment_type': self._extract_field(
                    job_data, None,
                    ['employmentType', 'type', 'jobType']
                ) or '',
                'date_posted': self._extract_field(
                    job_data, None,
                    ['datePosted', 'postedDate', 'publishedDate', 'createdAt']
                ) or ''
            }
            
            return job
            
        except Exception as e:
            print(f"⚠️  Error parsing job item: {str(e)}")
            return None
    
    def _extract_field(
        self,
        data: Dict,
        configured_path: Any,
        fallback_keys: List[str]
    ) -> Any:
        """Extract a field from data using configured path or fallback keys."""
        # Try configured path first
        if configured_path:
            if isinstance(configured_path, list):
                # Nested path like ['addresses', 0, 'city']
                value = data
                for key in configured_path:
                    if isinstance(value, dict):
                        value = value.get(key)
                    elif isinstance(value, list) and isinstance(key, int):
                        if len(value) > key:
                            value = value[key]
                        else:
                            return None
                    else:
                        return None
                return value
            else:
                # Simple key
                return data.get(configured_path)
        
        # Try fallback keys
        for key in fallback_keys:
            if key in data:
                return data[key]
        
        return None


def scrape_with_config(
    company_slug: str,
    keywords: List[str] = None,
    location: str = "DEU"
) -> List[Dict]:
    """
    Convenience function to scrape jobs using saved configuration.
    
    Args:
        company_slug: Company identifier
        keywords: Search keywords
        location: Location filter
        
    Returns:
        List of jobs
    """
    scraper = DynamicAPIScraper()
    return scraper.scrape_jobs(company_slug, keywords, location)


if __name__ == "__main__":
    # Test the dynamic scraper
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dynamic_api_scraper.py <company_slug>")
        sys.exit(1)
    
    slug = sys.argv[1]
    jobs = scrape_with_config(slug, keywords=['intern', 'internship'])
    
    print(f"\n📋 Found {len(jobs)} jobs:")
    for job in jobs[:5]:  # Show first 5
        print(f"  • {job['title']} - {job['location']}")
