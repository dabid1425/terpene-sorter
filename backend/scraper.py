"""
Web scraper for cannabis products from shop.revcanna.com
Fetches product data (terpenes, cannabinoids, pricing) via the SweedPOS API.
"""

import json
import re
import time

import requests

from db import init_db, save_products as db_save_products, load_products as db_load_products

BASE_URL = "https://shop.revcanna.com"
LAB_API_URL = f"{BASE_URL}/_api/Products/GetExtendedLabdata"
PRODUCT_LIST_API_URL = f"{BASE_URL}/_api/Products/GetProductList"
STORE_ID = "235"
PAGE_SIZE = 100

_API_HEADERS = {
    'storeid': STORE_ID,
    'content-type': 'application/json',
    'ssr': 'false',
}


def _api_post(url, payload, retries=3, timeout=15):
    """POST to a SweedPOS API endpoint with exponential-backoff retries."""
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=_API_HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"Failed POST {url}: {e}")
                return None


def extract_variant_id(url):
    """Extract the numeric variant ID from a product URL."""
    match = re.search(r'-(\d+)(?:\?|$)', url)
    return int(match.group(1)) if match else None


def fetch_lab_data(variant_id):
    """Fetch full lab data (terpenes, cannabinoids) for a variant."""
    return _api_post(LAB_API_URL, {'variantId': variant_id})


def fetch_product_list_page(page_num, sale_type, page_size=PAGE_SIZE):
    """Fetch one page of products from the SweedPOS GetProductList API."""
    return _api_post(PRODUCT_LIST_API_URL, {
        'filters': {},
        'page': page_num,
        'pageSize': page_size,
        'sortingMethodId': 7,
        'searchTerm': '',
        'saleType': sale_type,
        'platformOs': 'web',
        'sourcePage': 1,
    })


def parse_product_list_item(product, variant):
    """Convert a product+variant pair from GetProductList into our product schema."""
    prevalence = (product.get('strain') or {}).get('prevalence') or {}
    strain_type = prevalence.get('name', '')

    price = float(variant.get('price') or 0)
    promo = variant.get('promoPrice')
    sale_price = float(promo) if promo is not None else 0.0
    if sale_price >= price:
        sale_price = 0.0

    lab = variant.get('labTests') or {}
    thc_vals = (lab.get('thc') or {}).get('value') or []
    thc = float(thc_vals[0]) if thc_vals else 0.0
    cbd_vals = (lab.get('cbd') or {}).get('value') or []
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
        'purchase_type': '',
    }


def _edible_mg_per_unit(weight):
    """Parse mg per unit from an edible weight string (e.g. '20mg 10pk', '10pk 100mg')."""
    pack_first = re.match(r'(\d+)pk\s+(\d+)mg', weight)
    if pack_first:
        return int(pack_first.group(2)) / int(pack_first.group(1))
    mg_first = re.match(r'(\d+)mg', weight)
    if mg_first:
        return int(mg_first.group(1))
    return 0


def _concentrate_grams(weight):
    """Parse grams from a concentrate weight string (e.g. '2g', '3.5g')."""
    match = re.match(r'([\d.]+)g', weight)
    return float(match.group(1)) if match else 0


def classify_purchase_type(product):
    """Determine purchase type from product attributes."""
    category = product.get('category', '')
    weight = product.get('weight', '')
    if category == 'Edibles' and _edible_mg_per_unit(weight) > 10:
        return 'Medical'
    if category == 'Concentrates' and _concentrate_grams(weight) > 1:
        return 'Medical'
    return 'Recreational'


def fetch_all_products_api():
    """Fetch all products in a single Medical pull and classify by purchase type."""
    products = {}
    page = 1
    while True:
        print(f"Fetching product list page {page}...")
        data = fetch_product_list_page(page, 'Medical')
        if not data:
            break
        items = data.get('list', [])
        total = data.get('total', 0)
        for item in items:
            for variant in item.get('variants', []):
                product = parse_product_list_item(item, variant)
                if product['name']:
                    product['purchase_type'] = classify_purchase_type(product)
                    products[product['variant_id']] = product
        print(f"  Got {len(items)} items (running total: {len(products)} variants)")
        if page * PAGE_SIZE >= total or not items:
            break
        page += 1
    return list(products.values())


def scrape_all_products():
    """Fetch all products from the API and enrich each with lab terpene data."""
    init_db()
    print("Fetching all products from SweedPOS API...")
    all_products = fetch_all_products_api()
    print(f"Fetched {len(all_products)} product variants")

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
            for entry in lab['terpenes'].get('values', []):
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
    """Return a sorted list of all terpene names found across products."""
    products = load_products()
    terpene_set = set()
    for product in products:
        terpene_set.update(product.get('terpenes', {}).keys())
    return sorted(terpene_set)


if __name__ == "__main__":
    products = scrape_all_products()
    print(f"\nScraped {len(products)} products")
    if products:
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
