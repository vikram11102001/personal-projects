"""
Automatic API Discovery Module

This module automatically discovers job board APIs by:
1. Visiting the career page with Playwright
2. Intercepting all network requests (XHR/Fetch)
3. Identifying job-related API calls using heuristics
4. Extracting endpoint, headers, authentication, and payload
5. Saving discovered configuration for reuse
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Request, Response
from urllib.parse import urlparse


class APIDiscovery:
    """Discovers job board APIs automatically from career page URLs."""
    
    def __init__(self):
        self.captured_requests: List[Dict] = []
        self.job_api_keywords = [
            'job', 'career', 'position', 'vacancy', 'search', 'opening',
            'employment', 'recruit', 'applicant', 'candidate'
        ]
    
    async def discover_api(self, career_url: str, timeout: int = 90000) -> Optional[Dict]:
        """
        Discover job API from a career page URL.
        
        Args:
            career_url: The career page URL to analyze
            timeout: Maximum time to wait for page load (ms) - default 90 seconds
            
        Returns:
            Dictionary with API configuration or None if not found
        """
        print(f"🔍 Discovering API for: {career_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                ignore_https_errors=True  # Fix SSL certificate issues (e.g., Infineon)
            )
            page = await context.new_page()
            
            # Set up request/response interceptors
            page.on("request", self._on_request)
            page.on("response", self._on_response)
            
            try:
                print(f"📄 Loading career page...")
                # Use longer timeout and wait for network to be idle
                await page.goto(career_url, timeout=timeout, wait_until='networkidle')
                
                # Wait additional time for lazy-loaded content
                print(f"⏳ Waiting for dynamic content...")
                await page.wait_for_timeout(5000)
                
                # Try to interact with the page to trigger API calls
                await self._trigger_api_calls(page)
                
                # Analyze captured requests
                api_config = self._analyze_requests(career_url)
                
                await browser.close()
                
                if api_config:
                    print(f"✅ Successfully discovered API!")
                    return api_config
                else:
                    print(f"❌ No job API found")
                    return None
                    
            except Exception as e:
                print(f"❌ Error during discovery: {str(e)}")
                await browser.close()
                return None
    
    def _on_request(self, request: Request):
        """Capture all requests."""
        # Only capture XHR and Fetch requests
        resource_type = request.resource_type
        if resource_type in ['xhr', 'fetch']:
            try:
                # Try to get post_data, but handle binary data gracefully
                post_data = None
                try:
                    post_data = request.post_data
                except UnicodeDecodeError:
                    # Skip binary data that can't be decoded as UTF-8
                    pass
                
                request_data = {
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': post_data,
                    'resource_type': resource_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
                self.captured_requests.append(request_data)
            except Exception as e:
                # Silently skip problematic requests
                pass
    
    async def _on_response(self, response: Response):
        """Capture response data for relevant requests."""
        try:
            # Only process JSON responses
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                url = response.url
                
                # Find the matching request
                for req in self.captured_requests:
                    if req['url'] == url and 'response_body' not in req:
                        try:
                            body = await response.json()
                            req['response_body'] = body
                            req['status_code'] = response.status
                        except:
                            pass
                        break
        except:
            pass
    
    async def _trigger_api_calls(self, page):
        """Try to trigger API calls by interacting with the page."""
        try:
            # Look for search boxes and trigger them
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[placeholder*="job" i]',
                'input[id*="search" i]',
                'input[class*="search" i]'
            ]
            
            for selector in search_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.fill('intern')
                        await page.wait_for_timeout(1000)
                        # Try to submit/trigger search
                        await element.press('Enter')
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Try clicking common filter buttons
            filter_selectors = [
                'button:has-text("Search")',
                'button:has-text("Filter")',
                'button:has-text("Apply")'
            ]
            
            for selector in filter_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        await page.wait_for_timeout(2000)
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Could not trigger additional API calls: {str(e)}")
    
    def _analyze_requests(self, career_url: str) -> Optional[Dict]:
        """
        Analyze captured requests to find job API.
        
        Uses heuristics to identify the most likely job API endpoint.
        """
        print(f"📊 Analyzing {len(self.captured_requests)} captured requests...")
        
        candidates = []
        
        for req in self.captured_requests:
            score = self._score_request(req, career_url)
            if score > 0:
                candidates.append({
                    'request': req,
                    'score': score
                })
        
        if not candidates:
            return None
        
        # Sort by score and take the best one
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        
        print(f"🎯 Found {len(candidates)} potential APIs, best score: {best['score']}")
        
        return self._extract_config(best['request'], career_url)
    
    def _score_request(self, request: Dict, career_url: str) -> int:
        """Score a request based on likelihood of being a job API."""
        score = 0
        url = request['url'].lower()
        
        # Check URL for job-related keywords
        for keyword in self.job_api_keywords:
            if keyword in url:
                score += 10
        
        # Prefer requests with response bodies
        if 'response_body' in request:
            score += 20
            
            response = request['response_body']
            
            # Check if response looks like a job listing
            if isinstance(response, dict):
                # Look for array of jobs
                if 'value' in response or 'data' in response or 'results' in response:
                    score += 15
                
                # Look for job-related fields
                response_str = json.dumps(response).lower()
                job_fields = ['title', 'location', 'position', 'description', 'salary']
                for field in job_fields:
                    if field in response_str:
                        score += 5
            
            elif isinstance(response, list):
                score += 10
                # If it's an array, check first item
                if len(response) > 0 and isinstance(response[0], dict):
                    item_str = json.dumps(response[0]).lower()
                    if any(field in item_str for field in ['title', 'job', 'position']):
                        score += 10
        
        # Prefer POST requests (more likely to be search APIs)
        if request['method'] == 'POST':
            score += 5
        
        # Check for API authentication headers
        headers = request['headers']
        auth_headers = ['api-key', 'x-api-key', 'authorization', 'apikey']
        for header in auth_headers:
            if header in headers:
                score += 15
        
        return score
    
    def _extract_config(self, request: Dict, career_url: str) -> Dict:
        """Extract API configuration from a request."""
        headers = request['headers']
        
        # Extract important headers (authentication, content-type, referer)
        important_headers = {}
        header_patterns = ['api-key', 'x-api-key', 'authorization', 'content-type', 'apikey']
        
        for key, value in headers.items():
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in header_patterns):
                important_headers[key] = value
        
        # Always include referer
        important_headers['referer'] = career_url
        
        # Parse payload if it's a POST request
        payload_template = None
        if request['method'] == 'POST' and request.get('post_data'):
            try:
                payload_template = json.loads(request['post_data'])
            except:
                payload_template = request['post_data']
        
        # Extract response sample
        response_sample = None
        if 'response_body' in request:
            response_sample = request['response_body']
        
        config = {
            'endpoint': request['url'],
            'method': request['method'],
            'headers': important_headers,
            'payload_template': payload_template,
            'response_sample': response_sample,
            'discovered_at': datetime.utcnow().isoformat() + 'Z',
            'career_url': career_url
        }
        
        return config


async def discover_company_api(url: str) -> Optional[Dict]:
    """
    Convenience function to discover API for a company career page.
    
    Args:
        url: Career page URL
        
    Returns:
        API configuration dictionary or None
    """
    discovery = APIDiscovery()
    return await discovery.discover_api(url)


if __name__ == "__main__":
    # Test the discovery
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python api_discovery.py <career_page_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    async def test():
        config = await discover_company_api(url)
        if config:
            print("\n🎉 API Configuration:")
            print(json.dumps(config, indent=2))
        else:
            print("\n❌ Could not discover API")
    
    asyncio.run(test())
