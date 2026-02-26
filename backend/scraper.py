"""
Web scraper for cannabis products from shop.revcanna.com
Extracts product data including terpene profiles.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import requests
import json
import os
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://shop.revcanna.com"
MENU_URL = f"{BASE_URL}/abingdon"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "products.json")
LAB_API_URL = f"{BASE_URL}/_api/Products/GetExtendedLabdata"
STORE_ID = "235"

# Common terpenes to track
TERPENES = [
    "myrcene", "limonene", "caryophyllene", "pinene", "alpha-pinene",
    "beta-pinene", "linalool", "humulene", "camphene", "terpinolene",
    "ocimene", "bisabolol", "terpineol", "nerolidol", "guaiol",
    "valencene", "geraniol", "eucalyptol", "borneol", "fenchol"
]

def get_browser(playwright):
    """Launch a headless Chromium browser instance."""
    browser = playwright.chromium.launch(headless=True)
    return browser


def fetch_page(browser, url, retries=3, wait_until='load'):
    """Fetch a fully-rendered page using Playwright with retry logic."""
    for attempt in range(retries):
        page = browser.new_page()
        try:
            page.goto(url, wait_until=wait_until, timeout=30000)
            return page.content()
        except PlaywrightTimeoutError:
            # networkidle times out on pages with persistent background requests.
            # Return whatever content has rendered rather than failing.
            if wait_until == 'networkidle':
                try:
                    content = page.content()
                    if content:
                        return content
                except Exception:
                    pass
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Timeout fetching {url}")
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Failed to fetch {url}: {e}")
                return None
        finally:
            page.close()
    return None


def extract_variant_id(url):
    """Extract the numeric variant ID from a product URL."""
    match = re.search(r'-(\d+)(?:\?|$)', url)
    return int(match.group(1)) if match else None


def fetch_lab_data(variant_id, retries=3):
    """Fetch full lab data (terpenes, cannabinoids) for a variant via the SweedPOS API."""
    for attempt in range(retries):
        try:
            response = requests.post(
                LAB_API_URL,
                headers={
                    'storeid': STORE_ID,
                    'content-type': 'application/json',
                    'ssr': 'false',
                },
                json={'variantId': variant_id},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Failed to fetch lab data for variant {variant_id}: {e}")
                return None
    return None


def extract_terpene_value(text):
    """Extract numeric terpene percentage from text."""
    if not text:
        return 0.0
    match = re.search(r'([\d.]+)\s*%?', str(text))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    return 0.0


def parse_product_page(browser, product_url, basic_info):
    """Parse a product detail page for terpene data."""
    html = fetch_page(browser, product_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    product = basic_info.copy()
    product['url'] = product_url
    product['terpenes'] = {}
    product['total_terpenes'] = 0.0

    # Look for terpene data in various possible locations
    # This may need adjustment based on actual site structure

    # Try to find terpene section
    terpene_section = soup.find(['div', 'section', 'table'],
                                 class_=lambda x: x and 'terpene' in x.lower() if x else False)

    if not terpene_section:
        # Try looking for terpene mentions in text
        terpene_section = soup.find(text=re.compile(r'terpene', re.I))
        if terpene_section:
            terpene_section = terpene_section.find_parent(['div', 'section', 'table'])

    # Also search the entire page for terpene data
    page_text = soup.get_text().lower()

    for terpene in TERPENES:
        # Look for patterns like "Myrcene: 0.5%" or "Myrcene 0.5%"
        pattern = rf'{terpene}\s*[:=]?\s*([\d.]+)\s*%?'
        match = re.search(pattern, page_text)
        if match:
            try:
                value = float(match.group(1))
                product['terpenes'][terpene] = value
            except ValueError:
                pass

    # Look for structured data (JSON-LD, data attributes, etc.)
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            # Check if terpene data is in structured data
            if isinstance(data, dict):
                for key, value in data.items():
                    key_lower = key.lower()
                    for terpene in TERPENES:
                        if terpene in key_lower:
                            product['terpenes'][terpene] = extract_terpene_value(value)
        except (json.JSONDecodeError, TypeError):
            pass

    # Look for data in tables
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                for terpene in TERPENES:
                    if terpene in label:
                        product['terpenes'][terpene] = extract_terpene_value(value)

    # Look for definition lists
    dls = soup.find_all('dl')
    for dl in dls:
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        for dt, dd in zip(dts, dds):
            label = dt.get_text().strip().lower()
            value = dd.get_text().strip()
            for terpene in TERPENES:
                if terpene in label:
                    product['terpenes'][terpene] = extract_terpene_value(value)

    # Look for THC/CBD content
    thc_match = re.search(r'thc\s*[:=]?\s*([\d.]+)\s*%?', page_text)
    if thc_match:
        try:
            product['thc'] = float(thc_match.group(1))
        except ValueError:
            product['thc'] = 0.0

    cbd_match = re.search(r'cbd\s*[:=]?\s*([\d.]+)\s*%?', page_text)
    if cbd_match:
        try:
            product['cbd'] = float(cbd_match.group(1))
        except ValueError:
            product['cbd'] = 0.0

    # Calculate total terpenes
    product['total_terpenes'] = sum(product['terpenes'].values())

    # Try to get product image
    img = soup.find('img', class_=lambda x: x and ('product' in x.lower() or 'main' in x.lower()) if x else False)
    if not img:
        img = soup.find('img', src=lambda x: x and 'product' in x.lower() if x else False)
    if img and img.get('src'):
        product['image'] = urljoin(product_url, img['src'])

    return product


def get_product_links(browser):
    """Get all product links from the menu page."""
    html = fetch_page(browser, MENU_URL, wait_until='networkidle')
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    products = []

    # Look for product cards/links - adjust selectors based on actual site structure
    # Common patterns for product listings
    product_selectors = [
        'a[href*="/product"]',
        'a[href*="/item"]',
        '.product-card a',
        '.product-link',
        '.menu-item a',
        '[data-product] a',
        '.product a',
    ]

    product_links = set()

    for selector in product_selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(BASE_URL, href)
                if '/product' in full_url or '/item' in full_url:
                    product_links.add(full_url)

    # Also look for any links that might be products
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link['href']
        full_url = urljoin(BASE_URL, href)
        # Look for product-like URLs
        if re.search(r'/(?:product|item|menu)/[^/]+', full_url):
            product_links.add(full_url)

    # Extract basic info from cards if available
    for link in product_links:
        product_info = {
            'name': '',
            'brand': '',
            'category': '',
            'strain_type': '',
            'price': 0.0,
            'weight': '',
            'thc': 0.0,
            'cbd': 0.0,
            'image': '',
        }
        products.append((link, product_info))

    return products


def scrape_menu_page(browser):
    """Scrape products directly from the menu page."""
    html = fetch_page(browser, MENU_URL, wait_until='networkidle')
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    products = []

    # Look for product containers
    product_containers = soup.find_all(['div', 'article', 'li'],
                                        class_=lambda x: x and any(term in x.lower() for term in ['product', 'item', 'card']) if x else False)

    for container in product_containers:
        product = {
            'name': '',
            'brand': '',
            'category': '',
            'strain_type': '',
            'price': 0.0,
            'weight': '',
            'thc': 0.0,
            'cbd': 0.0,
            'image': '',
            'url': '',
            'terpenes': {},
            'total_terpenes': 0.0,
        }

        # Extract name
        name_elem = container.find(['h2', 'h3', 'h4', 'span', 'a'],
                                   class_=lambda x: x and 'name' in x.lower() if x else False)
        if not name_elem:
            name_elem = container.find(['h2', 'h3', 'h4'])
        if name_elem:
            product['name'] = name_elem.get_text().strip()

        # Extract price
        price_elem = container.find(['span', 'div'],
                                    class_=lambda x: x and 'price' in x.lower() if x else False)
        if price_elem:
            price_text = price_elem.get_text()
            price_match = re.search(r'\$?([\d.]+)', price_text)
            if price_match:
                try:
                    product['price'] = float(price_match.group(1))
                except ValueError:
                    pass

        # Extract THC/CBD
        text = container.get_text().lower()
        thc_match = re.search(r'thc\s*[:=]?\s*([\d.]+)\s*%?', text)
        if thc_match:
            try:
                product['thc'] = float(thc_match.group(1))
            except ValueError:
                pass

        cbd_match = re.search(r'cbd\s*[:=]?\s*([\d.]+)\s*%?', text)
        if cbd_match:
            try:
                product['cbd'] = float(cbd_match.group(1))
            except ValueError:
                pass

        # Extract strain type
        for strain in ['indica', 'sativa', 'hybrid']:
            if strain in text:
                product['strain_type'] = strain.capitalize()
                break

        # Extract category
        for category in ['flower', 'concentrate', 'vape', 'edible', 'pre-roll', 'cartridge']:
            if category in text:
                product['category'] = category.capitalize()
                break

        # Extract image
        img = container.find('img')
        if img and img.get('src'):
            product['image'] = urljoin(MENU_URL, img['src'])

        # Extract link
        link = container.find('a', href=True)
        if link:
            product['url'] = urljoin(MENU_URL, link['href'])

        # Extract terpenes if present on the page
        for terpene in TERPENES:
            pattern = rf'{terpene}\s*[:=]?\s*([\d.]+)\s*%?'
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1))
                    product['terpenes'][terpene] = value
                except ValueError:
                    pass

        product['total_terpenes'] = sum(product['terpenes'].values())

        if product['name']:
            products.append(product)

    return products


def scrape_all_products():
    """Main function to scrape all products."""
    all_products = []

    print("Starting scrape of shop.revcanna.com/abingdon...")

    with sync_playwright() as playwright:
        browser = get_browser(playwright)
        try:
            # Get products from the fully-rendered menu page
            menu_products = scrape_menu_page(browser)
            print(f"Found {len(menu_products)} products on menu page")

            if menu_products:
                all_products = menu_products

            # Get product URLs (also from menu page)
            product_links = get_product_links(browser)
            print(f"Found {len(product_links)} product links")

            # Visit individual product pages for any fields not on the menu
            for i, (url, basic_info) in enumerate(product_links[:50]):
                print(f"Scraping product {i+1}/{min(len(product_links), 50)}: {url}")
                product = parse_product_page(browser, url, basic_info)
                if product:
                    existing = next((p for p in all_products if p['url'] == url), None)
                    if existing:
                        existing.update(product)
                    else:
                        all_products.append(product)
                time.sleep(0.5)
        finally:
            browser.close()

    # Enrich every product with full terpene data from the lab API
    print(f"\nFetching terpene lab data for {len(all_products)} products...")
    for i, product in enumerate(all_products):
        url = product.get('url', '')
        if not url:
            continue
        variant_id = extract_variant_id(url)
        if not variant_id:
            continue
        print(f"  [{i+1}/{len(all_products)}] variant {variant_id}")
        lab = fetch_lab_data(variant_id)
        if lab and 'terpenes' in lab:
            terpenes = {}
            total = 0.0
            for entry in lab['terpenes']['values']:
                name = entry['name'].lower()
                value = entry['min']
                if name == 'total terpenes':
                    total = value
                else:
                    terpenes[name] = value
            product['terpenes'] = terpenes
            product['total_terpenes'] = total
        time.sleep(0.2)

    save_products(all_products)
    return all_products


def save_products(products):
    """Save products to JSON file, filtering out junk entries."""
    valid = [p for p in products if p.get('name')]
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(valid, f, indent=2)
    print(f"Saved {len(valid)} products to {DATA_FILE} ({len(products) - len(valid)} junk entries filtered)")


def load_products():
    """Load products from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def get_all_terpenes():
    """Get a list of all terpenes found in products."""
    products = load_products()
    terpene_set = set()
    for product in products:
        terpene_set.update(product.get('terpenes', {}).keys())
    return sorted(list(terpene_set))


if __name__ == "__main__":
    products = scrape_all_products()
    print(f"\nScraped {len(products)} products")
    if products:
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
