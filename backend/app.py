"""
Flask API server for Terpene Sorter web app.
Provides endpoints for product data with terpene information.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import scrape_all_products, load_products, get_all_terpenes, save_products
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend


@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Get all products with optional sorting and filtering.

    Query parameters:
    - sort_by: Field to sort by (e.g., 'total_terpenes', 'myrcene', 'limonene', etc.)
    - sort_order: 'asc' or 'desc' (default: 'desc')
    - category: Filter by category (e.g., 'Flower', 'Concentrate')
    - strain_type: Filter by strain type (e.g., 'Indica', 'Sativa', 'Hybrid')
    - terpenes: Comma-separated list of terpenes to filter by (products must contain all)
    - min_thc: Minimum THC percentage
    - max_thc: Maximum THC percentage
    """
    products = load_products()

    # Apply filters
    category = request.args.get('category')
    if category:
        products = [p for p in products if p.get('category', '').lower() == category.lower()]

    strain_type = request.args.get('strain_type')
    if strain_type:
        products = [p for p in products if p.get('strain_type', '').lower() == strain_type.lower()]

    terpenes_filter = request.args.get('terpenes')
    if terpenes_filter:
        required_terpenes = [t.strip().lower() for t in terpenes_filter.split(',')]
        filtered_products = []
        for product in products:
            product_terpenes = {k.lower(): v for k, v in product.get('terpenes', {}).items()}
            if all(t in product_terpenes and product_terpenes[t] > 0 for t in required_terpenes):
                filtered_products.append(product)
        products = filtered_products

    min_thc = request.args.get('min_thc', type=float)
    if min_thc is not None:
        products = [p for p in products if p.get('thc', 0) >= min_thc]

    max_thc = request.args.get('max_thc', type=float)
    if max_thc is not None:
        products = [p for p in products if p.get('thc', 0) <= max_thc]

    # Apply sorting
    sort_by = request.args.get('sort_by', 'total_terpenes')
    sort_order = request.args.get('sort_order', 'desc')
    reverse = sort_order.lower() == 'desc'

    def get_sort_value(product):
        if sort_by == 'total_terpenes':
            return product.get('total_terpenes', 0)
        elif sort_by == 'thc':
            return product.get('thc', 0)
        elif sort_by == 'cbd':
            return product.get('cbd', 0)
        elif sort_by == 'price':
            return product.get('price', 0)
        elif sort_by == 'name':
            return product.get('name', '').lower()
        else:
            # Sort by specific terpene
            return product.get('terpenes', {}).get(sort_by, 0)

    try:
        products = sorted(products, key=get_sort_value, reverse=reverse)
    except TypeError:
        pass

    return jsonify({
        'products': products,
        'total': len(products)
    })


@app.route('/api/refresh', methods=['GET', 'POST'])
def refresh_products():
    """
    Trigger a fresh scrape of product data.
    Returns the newly scraped products.
    """
    try:
        products = scrape_all_products()
        return jsonify({
            'success': True,
            'message': f'Successfully scraped {len(products)} products',
            'products': products,
            'total': len(products)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/terpenes', methods=['GET'])
def get_terpenes():
    """
    Get a list of all available terpenes found in products.
    """
    terpenes = get_all_terpenes()
    return jsonify({
        'terpenes': terpenes
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    Get a list of all product categories.
    """
    products = load_products()
    categories = set()
    for product in products:
        category = product.get('category')
        if category:
            categories.add(category)
    return jsonify({
        'categories': sorted(list(categories))
    })


@app.route('/api/strain-types', methods=['GET'])
def get_strain_types():
    """
    Get a list of all strain types.
    """
    products = load_products()
    strain_types = set()
    for product in products:
        strain_type = product.get('strain_type')
        if strain_type:
            strain_types.add(strain_type)
    return jsonify({
        'strain_types': sorted(list(strain_types))
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about the product data.
    """
    products = load_products()

    if not products:
        return jsonify({
            'total_products': 0,
            'products_with_terpenes': 0,
            'categories': [],
            'strain_types': [],
            'terpene_averages': {}
        })

    products_with_terpenes = [p for p in products if p.get('terpenes') and sum(p['terpenes'].values()) > 0]

    # Calculate terpene averages
    terpene_totals = {}
    terpene_counts = {}
    for product in products_with_terpenes:
        for terpene, value in product.get('terpenes', {}).items():
            if value > 0:
                terpene_totals[terpene] = terpene_totals.get(terpene, 0) + value
                terpene_counts[terpene] = terpene_counts.get(terpene, 0) + 1

    terpene_averages = {}
    for terpene in terpene_totals:
        terpene_averages[terpene] = round(terpene_totals[terpene] / terpene_counts[terpene], 2)

    categories = set(p.get('category') for p in products if p.get('category'))
    strain_types = set(p.get('strain_type') for p in products if p.get('strain_type'))

    return jsonify({
        'total_products': len(products),
        'products_with_terpenes': len(products_with_terpenes),
        'categories': sorted(list(categories)),
        'strain_types': sorted(list(strain_types)),
        'terpene_averages': terpene_averages
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print("Starting Terpene Sorter API server...")
    print("API available at http://localhost:5001")
    print("\nEndpoints:")
    print("  GET /api/products   - Get all products (with optional filtering/sorting)")
    print("  GET /api/refresh    - Trigger a fresh scrape")
    print("  GET /api/terpenes   - List all available terpenes")
    print("  GET /api/categories - List all categories")
    print("  GET /api/strain-types - List all strain types")
    print("  GET /api/stats      - Get data statistics")
    app.run(host='0.0.0.0', port=5001, debug=True)
