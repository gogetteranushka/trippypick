#!/usr/bin/env python3
"""
Simplified TrippyPick scraper - directly scrape travel websites
"""

import os
import sys
import json
import logging
import argparse
import time

from backend.scrapers.web import WebsiteScraper
from backend.config import RAW_DIR, PROCESSED_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraping.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TrippyPick")

# List of travel websites to scrape
TRAVEL_WEBSITES = {
    "wanderon": {
        "url": "https://www.wanderon.in",
        "category": "Adventure/Group Tours",
        "popularity": "High"
    },
    "tripzygo": {
        "url": "https://www.tripzygo.in",
        "category": "Tour Packages",
        "popularity": "Medium"
    },
    "thrillophilia": {
        "url": "https://www.thrillophilia.com",
        "category": "Adventure/Activities",
        "popularity": "High"
    },
    "makemytrip": {
        "url": "https://www.makemytrip.com",
        "category": "OTA",
        "popularity": "Very High"
    },
    "yatra": {
        "url": "https://www.yatra.com",
        "category": "OTA",
        "popularity": "High"
    },
    "goibibo": {
        "url": "https://www.goibibo.com",
        "category": "OTA",
        "popularity": "High"
    },
    "traveltriangle": {
        "url": "https://traveltriangle.com",
        "category": "Marketplace",
        "popularity": "Medium"
    },
    "zostel": {
        "url": "https://www.zostel.com",
        "category": "Hostels/Backpacking",
        "popularity": "Medium"
    },
    "veenaworld": {
        "url": "https://www.veenaworld.com",
        "category": "Tour Operator",
        "popularity": "Medium"
    },
    "thomascook": {
        "url": "https://www.thomascook.in",
        "category": "Tour Operator",
        "popularity": "Medium"
    },
    "kesari": {
        "url": "https://www.kesari.in",
        "category": "Tour Operator",
        "popularity": "Medium"
    },
    "sotc": {
        "url": "https://www.sotc.in",
        "category": "Tour Operator",
        "popularity": "Medium"
    }
}

def load_websites_list(file_path=None):
    """Load websites from file or use default list"""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return TRAVEL_WEBSITES

def scrape_websites(websites_dict):
    """Scrape travel websites for package information"""
    website_scraper = WebsiteScraper(output_dir=RAW_DIR)
    results = {}
    
    try:
        for name, info in websites_dict.items():
            url = info['url']
            logger.info(f"Scraping {name}: {url}")
            
            try:
                website_data = website_scraper.scrape(url)
                if website_data:
                    # Add metadata
                    website_data['company_name'] = name
                    website_data['category'] = info.get('category', 'Unknown')
                    website_data['popularity'] = info.get('popularity', 'Unknown')
                    results[name] = website_data
                    
                    # Log summary
                    packages_count = len(website_data.get('packages', []))
                    logger.info(f"✓ Found {packages_count} packages from {name}")
                    
            except Exception as e:
                logger.error(f"Error scraping {name}: {e}")
                continue
            
            # Delay between sites
            time.sleep(5)
            
    finally:
        website_scraper.close()
    
    return results

def analyze_results(results):
    """Analyze and summarize scraped data"""
    total_websites = len(results)
    total_packages = sum(len(data.get('packages', [])) for data in results.values())
    
    by_category = {}
    for name, data in results.items():
        category = data.get('category', 'Unknown')
        if category not in by_category:
            by_category[category] = {'count': 0, 'packages': 0}
        by_category[category]['count'] += 1
        by_category[category]['packages'] += len(data.get('packages', []))
    
    # Find popular destinations
    destinations = {}
    for data in results.values():
        for package in data.get('packages', []):
            dest = package.get('destination')
            if dest:
                destinations[dest] = destinations.get(dest, 0) + 1
    
    popular_destinations = sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Price range analysis
    prices = []
    for data in results.values():
        for package in data.get('packages', []):
            price = package.get('price')
            if price:
                # Extract numeric price
                import re
                price_match = re.search(r'(\d+)', price.replace(',', ''))
                if price_match:
                    prices.append(int(price_match.group(1)))
    
    return {
        'total_websites': total_websites,
        'total_packages': total_packages,
        'by_category': by_category,
        'popular_destinations': popular_destinations,
        'price_range': {
            'min': min(prices) if prices else 0,
            'max': max(prices) if prices else 0,
            'avg': sum(prices) // len(prices) if prices else 0
        }
    }

def main():
    parser = argparse.ArgumentParser(description="TrippyPick Travel Package Scraper")
    parser.add_argument('--websites', nargs='+', help="Specific websites to scrape")
    parser.add_argument('--category', help="Scrape only specific category")
    parser.add_argument('--analyze', action='store_true', help="Analyze existing data")
    parser.add_argument('--file', help="Load websites from JSON file")
    
    args = parser.parse_args()
    
    # Create directories
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    if args.analyze:
        # Analyze existing data
        try:
            with open(os.path.join(RAW_DIR, 'website_packages.json'), 'r') as f:
                results = json.load(f)
                analysis = analyze_results(results)
                
                print("\n=== Scraping Analysis ===")
                print(f"Total websites scraped: {analysis['total_websites']}")
                print(f"Total packages found: {analysis['total_packages']}")
                
                print("\nBy Category:")
                for cat, data in analysis['by_category'].items():
                    print(f"  {cat}: {data['count']} sites, {data['packages']} packages")
                
                print("\nPopular Destinations:")
                for dest, count in analysis['popular_destinations']:
                    print(f"  {dest}: {count} packages")
                
                print(f"\nPrice Range: ₹{analysis['price_range']['min']:,} - ₹{analysis['price_range']['max']:,}")
                print(f"Average Price: ₹{analysis['price_range']['avg']:,}")
                
        except FileNotFoundError:
            print("No data found. Run scraper first.")
        return
    
    # Load websites
    websites = load_websites_list(args.file)
    
    # Filter by category if specified
    if args.category:
        websites = {k: v for k, v in websites.items() if v.get('category') == args.category}
    
    # Filter specific websites if specified
    if args.websites:
        websites = {k: v for k, v in websites.items() if k in args.websites}
    
    if not websites:
        logger.error("No websites to scrape")
        return
    
    logger.info(f"Starting to scrape {len(websites)} websites...")
    
    # Scrape websites
    results = scrape_websites(websites)
    
    # Save results
    output_file = os.path.join(RAW_DIR, 'website_packages.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Results saved to {output_file}")
    
    # Show summary
    analysis = analyze_results(results)
    print(f"\n✓ Scraped {analysis['total_websites']} websites")
    print(f"✓ Found {analysis['total_packages']} packages")
    print(f"✓ Price range: ₹{analysis['price_range']['min']:,} - ₹{analysis['price_range']['max']:,}")

if __name__ == "__main__":
    main()