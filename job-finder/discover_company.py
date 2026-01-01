#!/usr/bin/env python3
"""
Standalone tool to discover and save API configuration for a new company.

Usage:
    python discover_company.py "https://careers.siemens.com/" --name "Siemens"
    python discover_company.py "https://www.bmwgroup.jobs/" --name "BMW"
"""

import asyncio
import argparse
import json
import re
from src.api_discovery import discover_company_api
from src.dynamic_api_scraper import DynamicAPIScraper


def slugify(name: str) -> str:
    """Convert company name to slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


async def main():
    parser = argparse.ArgumentParser(
        description='Discover and save API configuration for a company'
    )
    parser.add_argument(
        'url',
        help='Career page URL (e.g., https://careers.siemens.com/)'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Company name (e.g., "Siemens")'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the discovered API by making a sample request'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"🔍 API Discovery Tool")
    print("=" * 60)
    print(f"Company: {args.name}")
    print(f"URL: {args.url}")
    print()
    
    # Discover the API
    config = await discover_company_api(args.url)
    
    if not config:
        print("\n❌ Failed to discover API")
        print("💡 Tip: The website might not have a public API,")
        print("   or it might require authentication/cookies.")
        return
    
    # Prepare the configuration
    company_slug = slugify(args.name)
    config['company_name'] = args.name
    
    print(f"\n✅ Successfully discovered API!")
    print(f"\n📝 Configuration Preview:")
    print("-" * 60)
    print(f"Endpoint: {config['endpoint']}")
    print(f"Method: {config['method']}")
    print(f"Headers: {list(config['headers'].keys())}")
    if config.get('payload_template'):
        print(f"Payload: {type(config['payload_template']).__name__}")
    print("-" * 60)
    
    # Save the configuration
    scraper = DynamicAPIScraper()
    scraper.save_config(company_slug, config)
    
    print(f"\n💾 Saved configuration as: '{company_slug}'")
    print(f"   Location: src/api_configs.json")
    
    # Test if requested
    if args.test:
        print(f"\n🧪 Testing API call...")
        jobs = scraper.scrape_jobs(
            company_slug,
            keywords=['intern', 'internship'],
            location='DEU'
        )
        
        if jobs:
            print(f"\n✅ Test successful! Found {len(jobs)} jobs")
            print(f"\n📋 Sample jobs:")
            for job in jobs[:3]:
                print(f"  • {job['title']}")
                print(f"    📍 {job['location']}")
                if job['url']:
                    print(f"    🔗 {job['url']}")
                print()
        else:
            print("\n⚠️  Test call returned 0 jobs")
            print("   The API configuration might need manual adjustment")
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
    print(f"\n📌 Next steps:")
    print(f"1. Add to config.py:")
    print(f'   {{')
    print(f'       "name": "{args.name}",')
    print(f'       "slug": "{company_slug}",')
    print(f'       "url": "{args.url}",')
    print(f'       "keywords": ["intern", "internship"],')
    print(f'       "locations": ["Germany"]')
    print(f'   }}')
    print(f"\n2. Run main.py to start scraping automatically!")


if __name__ == "__main__":
    asyncio.run(main())
