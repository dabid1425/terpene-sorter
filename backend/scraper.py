"""
Web scraper for cannabis products from shop.revcanna.com
Extracts product data including terpene profiles, pricing, and weight.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import requests
import json
import os
import time
import re
from urllib.parse import urljoin

from db import init_db, save_products as db_save_products, load_products as db_load_products

BASE_URL = "https://shop.revcanna.com"
MENU_URL = f"{BASE_URL}/abingdon"
LAB_API_URL = f"{BASE_URL}/_api/Products/GetExtendedLabdata"
PRODUCT_LIST_API_URL = f"{BASE_URL}/_api/Products/GetProductList"
STORE_ID = "235"
PAGE_SIZE = 100

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


def extract_weight_from_url(url):
    """Extract weight from a product URL slug (e.g., '3.5g', '1oz', '500mg')."""
    match = re.search(r'-([\d.]+(?:g|oz|mg|lb))-\d+', url, re.I)
    return match.group(1).lower() if match else ''


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


def parse_api_product(raw):
    """Parse a raw SweedPOS API product dict into our product schema."""
    def get_str(keys):
        for k in keys:
            v = raw.get(k)
            if v is not None:
                return str(v).strip()
        return ''

    def get_float(keys):
        for k in keys:
            v = raw.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        return 0.0

    price = get_float(['price', 'basePrice', 'regularPrice', 'originalPrice'])
    sale_price = get_float([
        'salePrice', 'discountedPrice', 'discountPrice',
        'promotionPrice', 'onSalePrice', 'promoPrice',
    ])
    # Only keep sale_price when it's a genuine discount
    if sale_price >= price:
        sale_price = 0.0

    url = get_str(['url', 'link', 'href', 'productUrl', 'menuUrl'])
    weight = get_str(['weight', 'size', 'net_weight', 'netWeight', 'packageSize'])
    if not weight and url:
        weight = extract_weight_from_url(url)

    return {
        'name': get_str(['name', 'productName', 'title']),
        'brand': get_str(['brand', 'brandName', 'manufacturer']),
        'category': get_str(['category', 'categoryName', 'type', 'productType']),
        'strain_type': get_str(['strainType', 'strain_type', 'strain', 'subType']),
        'price': price,
        'sale_price': sale_price,
        'weight': weight,
        'thc': get_float(['thc', 'thcPercentage', 'thcContent', 'thcPercent']),
        'cbd': get_float(['cbd', 'cbdPercentage', 'cbdContent', 'cbdPercent']),
        'image': get_str(['image', 'imageUrl', 'thumbnail', 'photo', 'imgUrl']),
        'url': url,
        'terpenes': {},
        'total_terpenes': 0.0,
    }


def _enrich_product_from_api_item(product, api_item):
    """Overwrite price/sale_price/weight on a product with data from an intercepted API item."""
    def try_float(keys):
        for k in keys:
            v = api_item.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        return None

    def try_str(keys):
        for k in keys:
            v = api_item.get(k)
            if v is not None:
                s = str(v).strip()
                if s:
                    return s
        return None

    price = try_float(['price', 'basePrice', 'regularPrice', 'originalPrice'])
    if price is not None:
        product['price'] = price

    sale_price = try_float([
        'salePrice', 'discountedPrice', 'discountPrice',
        'promotionPrice', 'onSalePrice', 'promoPrice',
    ])
    if sale_price is not None and sale_price > 0 and sale_price < product.get('price', float('inf')):
        product['sale_price'] = sale_price

    weight = try_str(['weight', 'size', 'net_weight', 'netWeight', 'packageSize'])
    if weight and not product.get('weight'):
        product['weight'] = weight


def parse_product_page(browser, product_url, basic_info):
    """Parse a product detail page for terpene data."""
    html = fetch_page(browser, product_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    product = basic_info.copy()
    product['url'] = product_url
    product.setdefault('terpenes', {})
    product.setdefault('total_terpenes', 0.0)
    product.setdefault('sale_price', 0.0)
    if not product.get('weight'):
        product['weight'] = extract_weight_from_url(product_url)

    # Look for terpene data in various possible locations
    terpene_section = soup.find(
        ['div', 'section', 'table'],
        class_=lambda x: x and 'terpene' in x.lower() if x else False,
    )

    if not terpene_section:
        terpene_section = soup.find(text=re.compile(r'terpene', re.I))
        if terpene_section:
            terpene_section = terpene_section.find_parent(['div', 'section', 'table'])

    page_text = soup.get_text().lower()

    for terpene in TERPENES:
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

    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link['href']
        full_url = urljoin(BASE_URL, href)
        if re.search(r'/(?:product|item|menu)/[^/]+', full_url):
            product_links.add(full_url)

    for link in product_links:
        product_info = {
            'name': '',
            'brand': '',
            'category': '',
            'strain_type': '',
            'price': 0.0,
            'sale_price': 0.0,
            'weight': extract_weight_from_url(link),
            'thc': 0.0,
            'cbd': 0.0,
            'image': '',
        }
        products.append((link, product_info))

    return products


def scrape_menu_page(browser):
    """
    Scrape products from the menu page.

    Uses Playwright response interception to capture structured product data
    (including price and sale price) from SweedPOS API calls made by the page.
    Falls back to HTML parsing for any fields not available in the API.
    """
    # Keyed by str(variantId) — populated by the response handler below
    api_products_by_id = {}

    def handle_response(response):
        if '/_api/' not in response.url:
            return
        if response.status != 200:
            return
        try:
            content_type = response.headers.get('content-type', '')
            if 'json' not in content_type:
                return
            data = response.json()

            # The API may return a bare list or wrap it in a dict
            candidates = []
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                for key in ('products', 'items', 'data', 'result', 'results', 'menuProducts'):
                    val = data.get(key)
                    if isinstance(val, list) and val:
                        candidates = val
                        break

            if not (candidates and isinstance(candidates[0], dict)):
                return

            first = candidates[0]
            has_price = any(k in first for k in ('price', 'basePrice', 'regularPrice'))
            has_name = any(k in first for k in ('name', 'productName', 'title'))
            if not (has_price or has_name):
                return

            print(f"  [API] Captured {len(candidates)} products from {response.url}")
            for item in candidates:
                vid = (
                    item.get('variantId')
                    or item.get('id')
                    or item.get('productId')
                )
                if vid is not None:
                    api_products_by_id[str(vid)] = item
        except Exception:
            pass

    page = browser.new_page()
    page.on('response', handle_response)
    html = None
    try:
        page.goto(MENU_URL, wait_until='networkidle', timeout=45000)
        page.wait_for_timeout(2000)
        html = page.content()
    except PlaywrightTimeoutError:
        try:
            html = page.content()
        except Exception:
            pass
    except Exception as e:
        print(f"Warning during menu scrape: {e}")
    finally:
        page.close()

    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    products = []

    # Build a blank product dict with all expected fields
    def blank_product():
        return {
            'name': '',
            'brand': '',
            'category': '',
            'strain_type': '',
            'price': 0.0,
            'sale_price': 0.0,
            'weight': '',
            'thc': 0.0,
            'cbd': 0.0,
            'image': '',
            'url': '',
            'terpenes': {},
            'total_terpenes': 0.0,
        }

    product_containers = soup.find_all(
        ['div', 'article', 'li'],
        class_=lambda x: x and any(
            term in x.lower() for term in ['product', 'item', 'card']
        ) if x else False,
    )

    for container in product_containers:
        product = blank_product()

        # --- Name ---
        name_elem = container.find(
            ['h2', 'h3', 'h4', 'span', 'a'],
            class_=lambda x: x and 'name' in x.lower() if x else False,
        )
        if not name_elem:
            name_elem = container.find(['h2', 'h3', 'h4'])
        if name_elem:
            product['name'] = name_elem.get_text().strip()

        # --- Price (HTML fallback) ---
        # Collect all dollar amounts found inside price-labelled elements
        price_elems = container.find_all(
            ['span', 'div', 'p'],
            class_=lambda x: x and 'price' in x.lower() if x else False,
        )
        dollar_amounts = []
        for elem in price_elems:
            for m in re.finditer(r'\$\s*([\d.]+)', elem.get_text()):
                try:
                    dollar_amounts.append(float(m.group(1)))
                except ValueError:
                    pass

        # Look for struck-through original prices (sale indicators)
        strike_elems = container.find_all(
            ['s', 'del', 'span'],
            class_=lambda x: x and any(
                t in x.lower() for t in ['original', 'was', 'strike', 'old', 'regular', 'compare']
            ) if x else False,
        )
        struck_prices = []
        for elem in strike_elems:
            for m in re.finditer(r'\$\s*([\d.]+)', elem.get_text()):
                try:
                    struck_prices.append(float(m.group(1)))
                except ValueError:
                    pass

        if struck_prices:
            product['price'] = max(struck_prices)
            non_struck = [p for p in dollar_amounts if p < product['price']]
            if non_struck:
                product['sale_price'] = min(non_struck)
        elif len(dollar_amounts) >= 2:
            product['price'] = max(dollar_amounts)
            product['sale_price'] = min(dollar_amounts)
        elif len(dollar_amounts) == 1:
            product['price'] = dollar_amounts[0]

        # --- THC / CBD ---
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

        # --- Strain type ---
        for strain in ['indica', 'sativa', 'hybrid']:
            if strain in text:
                product['strain_type'] = strain.capitalize()
                break

        # --- Category ---
        for category in ['flower', 'concentrate', 'vape', 'edible', 'pre-roll', 'cartridge', 'tincture', 'topical']:
            if category in text:
                product['category'] = category.capitalize()
                break

        # --- Image ---
        img = container.find('img')
        if img and img.get('src'):
            product['image'] = urljoin(MENU_URL, img['src'])

        # --- URL and weight ---
        link = container.find('a', href=True)
        if link:
            product['url'] = urljoin(MENU_URL, link['href'])
            product['weight'] = extract_weight_from_url(product['url'])

        # --- Enrich with intercepted API data (higher confidence) ---
        if product['url']:
            variant_id = extract_variant_id(product['url'])
            if variant_id and str(variant_id) in api_products_by_id:
                _enrich_product_from_api_item(product, api_products_by_id[str(variant_id)])

        # --- Inline terpenes ---
        for terpene in TERPENES:
            pattern = rf'{terpene}\s*[:=]?\s*([\d.]+)\s*%?'
            match = re.search(pattern, text)
            if match:
                try:
                    product['terpenes'][terpene] = float(match.group(1))
                except ValueError:
                    pass
        product['total_terpenes'] = sum(product['terpenes'].values())

        if product['name']:
            products.append(product)

    # If HTML parsing yielded nothing but API interception got products, build from API data
    if not products and api_products_by_id:
        print(f"  HTML parsing found no products; building from {len(api_products_by_id)} API items")
        for item in api_products_by_id.values():
            product = parse_api_product(item)
            if product['name']:
                products.append(product)

    return products


def fetch_product_list_page(page_num, page_size=PAGE_SIZE):
    """Fetch one page of products from the SweedPOS GetProductList API."""
    for attempt in range(3):
        try:
            response = requests.post(
                PRODUCT_LIST_API_URL,
                headers={
                    'storeid': STORE_ID,
                    'content-type': 'application/json',
                    'ssr': 'false',
                },
                json={
                    'filters': {},
                    'page': page_num,
                    'pageSize': page_size,
                    'sortingMethodId': 7,
                    'searchTerm': '',
                    'saleType': 'Recreational',
                    'platformOs': 'web',
                    'sourcePage': 1,
                },
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                print(f"Failed to fetch product list page {page_num}: {e}")
                return None
    return None


def parse_product_list_item(product, variant):
    """Convert a product+variant pair from GetProductList into our product schema."""
    strain = product.get('strain') or {}
    prevalence = strain.get('prevalence') or {}
    strain_type = prevalence.get('name', '')

    price = float(variant.get('price') or 0)
    promo = variant.get('promoPrice')
    sale_price = float(promo) if promo is not None else 0.0
    if sale_price >= price:
        sale_price = 0.0

    lab = variant.get('labTests') or {}
    thc_data = lab.get('thc') or {}
    thc_vals = thc_data.get('value') or []
    thc = float(thc_vals[0]) if thc_vals else 0.0
    cbd_data = lab.get('cbd') or {}
    cbd_vals = (cbd_data.get('value') or []) if cbd_data else []
    cbd = float(cbd_vals[0]) if cbd_vals else 0.0

    images = product.get('images') or variant.get('images') or []
    image = images[0] if images else ''

    brand_obj = product.get('brand') or {}
    brand = brand_obj.get('name', '') if isinstance(brand_obj, dict) else ''
    cat_obj = product.get('category') or {}
    category = cat_obj.get('name', '') if isinstance(cat_obj, dict) else ''

    return {
        'name': product.get('name', ''),
        'brand': brand,
        'category': category,
        'strain_type': strain_type,
        'price': price,
        'sale_price': sale_price,
        'weight': variant.get('name', ''),
        'thc': thc,
        'cbd': cbd,
        'image': image,
        'url': '',
        'variant_id': variant.get('id'),
        'terpenes': {},
        'total_terpenes': 0.0,
    }


def fetch_all_products_api():
    """Fetch all products from the SweedPOS GetProductList API (paginated)."""
    products = []
    page = 1
    while True:
        print(f"Fetching product list page {page}...")
        data = fetch_product_list_page(page)
        if not data:
            break
        items = data.get('list', [])
        total = data.get('total', 0)
        for item in items:
            for variant in item.get('variants', []):
                product = parse_product_list_item(item, variant)
                if product['name']:
                    products.append(product)
        print(f"  Got {len(items)} products (running total: {len(products)})")
        if page * PAGE_SIZE >= total or not items:
            break
        page += 1
    return products


def scrape_all_products():
    """Main function to scrape all products."""
    init_db()
    print("Fetching all products from SweedPOS API...")
    all_products = fetch_all_products_api()
    print(f"Fetched {len(all_products)} product variants")

    # Enrich every product with full terpene data from the lab API
    print(f"\nFetching terpene lab data for {len(all_products)} products...")
    for i, product in enumerate(all_products):
        variant_id = product.get('variant_id') or extract_variant_id(product.get('url', ''))
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
    """Upsert products into PostgreSQL."""
    db_save_products(products)


def load_products():
    """Load products from PostgreSQL."""
    return db_load_products()


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
