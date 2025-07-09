#!/usr/bin/env python3
"""
Test Instagram scraper separately
"""

import sys
import logging
from backend.scrapers.instagram import InstagramScraper
from backend.config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, RAW_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("instagram_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def test_without_login():
    """Test scraping without login (limited functionality)"""
    print("\n=== Testing Instagram Scraper WITHOUT Login ===")
    
    scraper = InstagramScraper(output_dir=RAW_DIR, headless=False)
    
    try:
        # Test a few profiles without login
        test_profiles = ["wanderon.in", "thrillophilia", "makemytrip"]
        
        for profile in test_profiles:
            print(f"\nTesting profile: {profile}")
            result = scraper.scrape_profile(profile)
            
            if result:
                print(f"✓ Username: {result['username']}")
                print(f"✓ Website: {result.get('website', 'Not found')}")
                bio = result.get('bio', 'Not extracted')
                print(f"✓ Bio: {bio[:100] if bio else 'Not extracted'}...")
            else:
                print(f"✗ Failed to scrape {profile}")
                
    finally:
        scraper.close()

def test_with_login():
    """Test scraping with login"""
    print("\n=== Testing Instagram Scraper WITH Login ===")
    
    # Get credentials
    username = INSTAGRAM_USERNAME or input("Instagram username: ")
    password = INSTAGRAM_PASSWORD or input("Instagram password: ")
    
    scraper = InstagramScraper(output_dir=RAW_DIR, headless=False)
    
    try:
        # Attempt login
        print("\nAttempting login...")
        if scraper.login(username, password):
            print("✓ Login successful!")
            
            # Test profile scraping
            test_profiles = ["wanderon.in", "nomadsofblr", "thrillophilia"]
            results = scraper.scrape_profiles(test_profiles)
            
            print(f"\n✓ Scraped {len(results)} profiles")
            
            # Show results
            for username, data in results.items():
                print(f"\n{username}:")
                print(f"  Website: {data.get('website', 'Not found')}")
                print(f"  Followers: {data.get('followers', 'Not found')}")
        else:
            print("✗ Login failed")
            print("\nTrying without login...")
            test_without_login()
            
    finally:
        scraper.close()

def test_single_profile(profile_name):
    """Test scraping a single profile"""
    print(f"\n=== Testing Single Profile: {profile_name} ===")
    
    scraper = InstagramScraper(output_dir=RAW_DIR, headless=False)
    
    try:
        result = scraper.scrape_profile(profile_name)
        
        if result:
            print("\nProfile Data:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Failed to scrape profile")
            
    finally:
        scraper.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Instagram scraper")
    parser.add_argument('--profile', help="Test specific profile")
    parser.add_argument('--no-login', action='store_true', help="Test without login")
    parser.add_argument('--login', action='store_true', help="Test with login")
    
    args = parser.parse_args()
    
    if args.profile:
        test_single_profile(args.profile)
    elif args.no_login:
        test_without_login()
    elif args.login:
        test_with_login()
    else:
        # Default: try without login first
        test_without_login()

if __name__ == "__main__":
    main()