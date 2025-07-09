import os
import json
import re
import time
import random
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from backend.scrapers.base import BaseScraper
from backend.config import HEADLESS_BROWSER, USER_AGENTS, PACKAGE_KEYWORDS, USE_SELENIUM_FOR_WEBSITES

from backend.scrapers.package_extractor import PackageExtractor


class WebsiteScraper(BaseScraper):
    """Scraper for travel agency websites"""
    
    def __init__(self, output_dir='data/raw', use_selenium=None, headless=None):
        """
        Initialize the website scraper
        
        Args:
            output_dir (str): Directory to save scraped data
            use_selenium (bool): Whether to use Selenium for JavaScript-heavy sites
            headless (bool): Whether to run Chrome in headless mode
        """
        super().__init__(output_dir)
        
        # Use config values if not specified
        self.use_selenium = USE_SELENIUM_FOR_WEBSITES if use_selenium is None else use_selenium
        self.headless = HEADLESS_BROWSER if headless is None else headless
        
        # Selenium setup
        self.driver = None
        
        # Data storage
        self.results = {}
    
    def _start_driver(self):
        """Start the Selenium WebDriver if not already running"""
        if self.driver is None and self.use_selenium:
            self.logger.info("Starting Chrome WebDriver for website scraping")
            
            # Set up Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set a random user agent
            user_agent = random.choice(USER_AGENTS)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
            
            # Execute script to hide webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def scrape(self, url):
        """
        Scrape a travel agency website to extract package information
        
        Args:
            url (str): Website URL to scrape
            
        Returns:
            dict: Extracted website data
        """
        # Basic URL validation and normalization
        if not url:
            self.logger.warning("Empty URL provided")
            return None
            
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            # Parse domain for identification
            domain = urlparse(url).netloc
            
            # Create structure for results
            website_data = {
                "url": url,
                "domain": domain,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "site_type": None,
                "packages": [],
                "error": None
            }
            
            # Fetch the main page
            self.logger.info(f"Fetching main page: {url}")
            html_content = self._fetch_page(url)
            if not html_content:
                website_data["error"] = "Could not fetch website content"
                self.logger.warning(f"Could not fetch content from {url}")
                return website_data
            
            # Identify site type
            site_type = self._identify_site_type(html_content, domain)
            website_data["site_type"] = site_type
            self.logger.info(f"Identified site type: {site_type}")
            
            # Find package pages
            package_urls = self._find_package_pages(html_content, url)
            self.logger.info(f"Found {len(package_urls)} potential package pages")
            
            # If no package URLs found, try to extract packages from the main page
            if not package_urls:
                self.logger.info("No package URLs found, checking main page for packages")
                package_data = self._extract_package_details(html_content, url, site_type)
                if package_data and (package_data.get("title") or package_data.get("description")):
                    website_data["packages"].append(package_data)
            else:
                # Extract packages from found URLs
                for i, package_url in enumerate(package_urls[:10]):  # Limit to 10 packages
                    self.logger.info(f"Extracting package {i+1}/{min(len(package_urls), 10)} from: {package_url}")
                    package_html = self._fetch_page(package_url)
                    if package_html:
                        package_data = self._extract_package_details(package_html, package_url, site_type)
                        if package_data and (package_data.get("title") or package_data.get("description")):
                            website_data["packages"].append(package_data)
                    
                    # Add random delay between requests
                    if i < min(len(package_urls), 10) - 1:
                        self.random_delay(2, 5)
            
            # Store results
            self.results[domain] = website_data
            
            # Save to file
            self._save_results()
            
            return website_data
            
        except Exception as e:
            self.logger.error(f"Error scraping website {url}: {e}")
            return {
                "url": url,
                "domain": urlparse(url).netloc if url else None,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "packages": []
            }
    
    def _fetch_page(self, url):
        """
        Fetch the HTML content of a page, using Selenium if necessary
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content if successful, None otherwise
        """
        if self.use_selenium:
            try:
                self._start_driver()
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Scroll to load lazy-loaded content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Get page source
                return self.driver.page_source
            except Exception as e:
                self.logger.error(f"Error fetching page with Selenium: {e}")
                # Fallback to requests
                return self.fetch_url(url)
        else:
            return self.fetch_url(url)
    
    def _identify_site_type(self, html_content, domain):
        """
        Identify the type of website
        
        Args:
            html_content (str): HTML content of the main page
            domain (str): Website domain
            
        Returns:
            str: Site type (wordpress, wix, custom, etc.)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        html_lower = html_content.lower()
        
        # Check for WordPress
        if (soup.select('meta[name="generator"][content*="WordPress"]') or 
            'wp-content' in html_lower or 
            'wordpress' in html_lower):
            return "wordpress"
        
        # Check for Wix
        if ('wix.com' in html_lower or 
            soup.select('meta[name="generator"][content*="Wix"]')):
            return "wix"
        
        # Check for Shopify
        if ('shopify' in html_lower or 
            soup.select('meta[name="generator"][content*="Shopify"]')):
            return "shopify"
        
        # Check for Squarespace
        if ('squarespace' in html_lower or 
            soup.select('meta[name="generator"][content*="Squarespace"]')):
            return "squarespace"
        
        # Check for travel-specific platforms
        if 'bookmytour' in html_lower or 'tourradar' in html_lower:
            return "travel_platform"
        
        # Default to custom
        return "custom"
    
    def _find_package_pages(self, html_content, base_url):
        """
        Find links to package pages on the website
        
        Args:
            html_content (str): HTML content of the main page
            base_url (str): Base URL of the website
            
        Returns:
            list: List of package page URLs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        package_urls = set()  # Use set to avoid duplicates
        
        # Parse base URL for comparison
        base_domain = urlparse(base_url).netloc
        
        # Look for links containing package-related keywords
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            link_text = link.text.strip().lower() if link.text else ""
            
            # Skip empty links, external links, and anchors
            if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'whatsapp:')):
                continue
            
            # Make URL absolute
            full_url = urljoin(base_url, href)
            
            # Skip external links
            if urlparse(full_url).netloc != base_domain:
                continue
            
            # Check if link or URL contains package keywords
            url_lower = full_url.lower()
            href_lower = href.lower()
            
            # Direct package indicators in URL
            package_url_indicators = ['package', 'tour', 'trip', 'itinerary', 'holiday', 'vacation', 'travel']
            if any(indicator in url_lower or indicator in href_lower for indicator in package_url_indicators):
                package_urls.add(full_url)
                continue
            
            # Check if link text contains package keywords
            if any(keyword in link_text for keyword in PACKAGE_KEYWORDS):
                package_urls.add(full_url)
        
        # If few package links found, look for common navigation patterns
        if len(package_urls) < 3:
            # Look for menu/navigation links
            nav_selectors = [
                'nav a', '.menu a', '.navigation a', '.navbar a', 
                'header a', '.header-menu a', '#menu a', '.nav-menu a'
            ]
            
            for selector in nav_selectors:
                nav_links = soup.select(selector)
                for link in nav_links:
                    href = link.get('href', '')
                    link_text = link.text.strip().lower() if link.text else ""
                    
                    if href and any(keyword in link_text for keyword in PACKAGE_KEYWORDS):
                        full_url = urljoin(base_url, href)
                        if urlparse(full_url).netloc == base_domain:
                            package_urls.add(full_url)
        
        # Convert set to list and sort for consistency
        return sorted(list(package_urls))
    
    def _extract_package_details(self, html_content, url, site_type):
        """
        Extract details of a travel package from its page
        
        Args:
            html_content (str): HTML content of the package page
            url (str): URL of the package page
            site_type (str): Type of website
            
        Returns:
            dict: Extracted package details
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize package data structure
        package_data = {
            "url": url,
            "title": None,
            "description": None,
            "destination": None,
            "duration": None,
            "price": None,
            "inclusions": [],
            "exclusions": [],
            "itinerary": [],
            "images": [],
            "highlights": []
        }
        
        # Extract title - improved logic
        title_selectors = ['h1', 'h2.title', 'h2.package-title', '.page-title', '.tour-title', '.package-name']
        for selector in title_selectors:
            title_elements = soup.select(selector)
            if title_elements:
                package_data["title"] = title_elements[0].text.strip()
                break
        
        # If no title found, use the most prominent heading
        if not package_data["title"]:
            headings = soup.find_all(['h1', 'h2', 'h3'])
            if headings:
                package_data["title"] = headings[0].text.strip()
        
        # Extract description - improved logic
        description_meta = soup.find('meta', attrs={'name': 'description'})
        if description_meta:
            package_data["description"] = description_meta.get('content', '').strip()
        
        if not package_data["description"] or len(package_data["description"]) < 50:
            # Look for description in common selectors
            description_selectors = [
                '.description', '.package-description', '.tour-description',
                '.content > p:first-of-type', 'article > p:first-of-type',
                '.overview', '.summary', '.intro', '.about-tour'
            ]
            
            for selector in description_selectors:
                desc_elements = soup.select(selector)
                if desc_elements:
                    text = ' '.join([elem.text.strip() for elem in desc_elements[:2]])
                    if len(text) > 50:  # Only use if substantial
                        package_data["description"] = text
                        break
        
        # Extract price with improved patterns
        price_text = self._extract_price(soup, html_content)
        if price_text:
            package_data["price"] = price_text
        
        # Extract duration with improved patterns
        duration_text = self._extract_duration(soup, html_content)
        if duration_text:
            package_data["duration"] = duration_text
        
        # Extract destination
        destination_text = self._extract_destination(soup, html_content, package_data["title"], url)
        if destination_text:
            package_data["destination"] = destination_text
        
        # Extract itinerary
        package_data["itinerary"] = self._extract_itinerary(soup)
        
        # Extract inclusions/exclusions
        package_data["inclusions"] = self._extract_list_items(soup, ['inclusion', 'included', 'include'])
        package_data["exclusions"] = self._extract_list_items(soup, ['exclusion', 'excluded', 'exclude', 'not included'])
        
        # Extract highlights
        package_data["highlights"] = self._extract_list_items(soup, ['highlight', 'feature', 'attraction'])
        
        # Extract images
        package_data["images"] = self._extract_images(soup, url)
        
        return package_data
    
    def _extract_price(self, soup, html_content):
        """Extract price information"""
        # Look for price in structured data
        price_selectors = [
            '.price', '.package-price', '.tour-price', '.cost',
            '.rate', '.amount', '[class*="price"]', '[class*="cost"]',
            '.pricing', '.tour-cost', '.package-cost'
        ]
        
        for selector in price_selectors:
            price_elements = soup.select(selector)
            for elem in price_elements:
                text = elem.text.strip()
                if re.search(r'[₹$€£]\s*\d+|Rs\.?\s*\d+|\d+\s*(?:INR|USD|EUR)', text, re.IGNORECASE):
                    return text
        
        # Use regex on full content
        price_patterns = [
            r'(?:Price|Cost|Fee|Rate|Starting from|From)[:\s]*(?:Rs\.?|INR|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:Rs\.?|INR|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Rs\.?|INR|₹)',
            r'(?:USD?|US\$|\$)\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # Return the first match with currency symbol
                match = matches[0]
                if isinstance(match, tuple):
                    match = match[0]
                return f"₹{match}"
        
        return None
    
    def _extract_duration(self, soup, html_content):
        """Extract duration information"""
        # Look for duration in common selectors
        duration_selectors = [
            '.duration', '.days', '.nights', '.package-duration',
            '.tour-duration', '[class*="duration"]', '[class*="days"]'
        ]
        
        for selector in duration_selectors:
            duration_elements = soup.select(selector)
            for elem in duration_elements:
                text = elem.text.strip()
                if re.search(r'\d+\s*(?:days?|nights?|D\s*\d*N)', text, re.IGNORECASE):
                    return text
        
        # Use regex patterns
        duration_patterns = [
            r'(\d+)\s*(?:days?|Days?)\s*(?:and|&)?\s*(\d+)?\s*(?:nights?|Nights?)',
            r'(\d+)\s*(?:nights?|Nights?)\s*(?:and|&)?\s*(\d+)?\s*(?:days?|Days?)',
            r'(\d+)D\s*(\d+)N',
            r'(\d+)\s*(?:Day|Night)(?:s)?\s+(?:Tour|Trip|Package)',
            r'Duration[:\s]*(\d+)\s*(?:days?|nights?)'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _extract_destination(self, soup, html_content, title, url):
        """Extract destination information"""
        # Try common selectors first
        destination_selectors = [
            '.destination', '.location', '.place', '[class*="destination"]',
            '[class*="location"]', '.tour-location', '.package-destination'
        ]
        
        for selector in destination_selectors:
            dest_elements = soup.select(selector)
            if dest_elements:
                return dest_elements[0].text.strip()
        
        # Try to extract from title
        if title:
            # Common patterns in titles
            dest_patterns = [
                r'(?:in|to|at)\s+([A-Za-z\s&\-\']+?)(?:\s*[-–—]|\s+Tour|\s+Trip|\s+Package|$)',
                r'^([A-Za-z\s&\-\']+?)\s+(?:Tour|Trip|Package|Vacation|Holiday)',
                r'(?:Tour|Trip|Package|Holiday)\s+(?:to|in)\s+([A-Za-z\s&\-\']+)'
            ]
            
            for pattern in dest_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    destination = match.group(1).strip()
                    # Clean up common suffixes
                    destination = re.sub(r'\s*(?:Tour|Trip|Package|Holiday)s?\s*$', '', destination, flags=re.IGNORECASE)
                    return destination
        
        # Try from URL
        url_parts = urlparse(url).path.strip('/').split('/')
        for part in url_parts:
            # Skip common non-destination parts
            if part.lower() in ['tour', 'tours', 'package', 'packages', 'trip', 'trips', 'destination', 'destinations']:
                continue
            # Clean and check if it looks like a destination
            cleaned = part.replace('-', ' ').replace('_', ' ').title()
            if len(cleaned) > 3 and cleaned.replace(' ', '').isalpha():
                return cleaned
        
        return None
    
    def _extract_itinerary(self, soup):
        """Extract itinerary information"""
        itinerary = []
        
        # Common itinerary selectors
        itinerary_selectors = [
            '.itinerary', '.day-by-day', '.schedule', '.tour-plan',
            '.trip-plan', '.daily-plan', '.day-wise', '[class*="itinerary"]'
        ]
        
        for selector in itinerary_selectors:
            itinerary_sections = soup.select(selector)
            if itinerary_sections:
                # Look for day-wise content
                day_patterns = [
                    r'Day\s*(\d+)',
                    r'(\d+)(?:st|nd|rd|th)\s+Day',
                    r'Day\s*[-–—]\s*(\d+)'
                ]
                
                # Try to find structured day elements
                for section in itinerary_sections:
                    day_elements = section.find_all(['h3', 'h4', 'h5', 'strong', 'b'])
                    
                    for elem in day_elements:
                        day_text = elem.text.strip()
                        for pattern in day_patterns:
                            if re.search(pattern, day_text, re.IGNORECASE):
                                # Get description
                                desc = ""
                                next_elem = elem.find_next_sibling()
                                if next_elem and next_elem.name in ['p', 'div', 'span']:
                                    desc = next_elem.text.strip()
                                
                                itinerary.append({
                                    "day": day_text,
                                    "description": desc
                                })
                                break
                
                if itinerary:
                    break
        
        return itinerary
    
    def _extract_list_items(self, soup, keywords):
        """Extract list items based on keywords"""
        items = []
        
        # Build selectors from keywords
        selectors = []
        for keyword in keywords:
            selectors.extend([
                f'.{keyword}', f'#{keyword}', f'[class*="{keyword}"]',
                f'h3:contains("{keyword.title()}")', f'h4:contains("{keyword.title()}")'
            ])
        
        for selector in selectors:
            try:
                sections = soup.select(selector)
                for section in sections:
                    # Look for list items nearby
                    parent = section.parent if section.name in ['h3', 'h4', 'h5'] else section
                    list_items = parent.find_all(['li', 'p'])
                    
                    for item in list_items[:10]:  # Limit to 10 items
                        text = item.text.strip()
                        if text and len(text) > 5 and text not in items:
                            items.append(text)
                    
                    if items:
                        return items
            except:
                continue
        
        return items
    
    def _extract_images(self, soup, base_url):
        """Extract image URLs"""
        images = []
        
        # Common image selectors for travel sites
        image_selectors = [
            '.gallery img', '.slider img', '.carousel img',
            '.package-image img', '.tour-image img', '.photos img',
            'article img', '.content img', '[class*="gallery"] img'
        ]
        
        for selector in image_selectors:
            img_elements = soup.select(selector)
            for img in img_elements[:10]:  # Limit to 10 images
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and not src.startswith('data:'):
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images
    
    def _save_results(self):
        """Save website scraping results to JSON file"""
        self.save_to_json(self.results, "website_packages.json")
    
    def close(self):
        """Close the WebDriver if using Selenium"""
        if self.driver:
            self.logger.info("Closing Chrome WebDriver")
            self.driver.quit()
            self.driver = None