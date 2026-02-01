# Terpene Sorter

A web app that scrapes cannabis products from shop.revcanna.com and displays them with terpene sorting/filtering capabilities.

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The API will be available at http://localhost:5000

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products` | GET | Get all products with optional filtering/sorting |
| `/api/refresh` | GET/POST | Trigger a fresh scrape |
| `/api/terpenes` | GET | List all available terpenes |
| `/api/categories` | GET | List all categories |
| `/api/strain-types` | GET | List all strain types |
| `/api/stats` | GET | Get data statistics |

### Query Parameters for `/api/products`

- `sort_by`: Field to sort by (e.g., 'total_terpenes', 'myrcene', 'thc', 'price')
- `sort_order`: 'asc' or 'desc' (default: 'desc')
- `category`: Filter by category
- `strain_type`: Filter by strain type
- `terpenes`: Comma-separated list of required terpenes
- `min_thc`: Minimum THC percentage
- `max_thc`: Maximum THC percentage

## Features

- **Sort by single terpene**: Select any terpene to sort products by that terpene's percentage
- **Sort by total terpenes**: Sort products by total terpene content
- **Multi-terpene filter**: Filter products that contain all selected terpenes
- **Category filter**: Filter by flower, concentrates, vapes, etc.
- **Strain type filter**: Filter by Indica, Sativa, or Hybrid
- **THC range filter**: Filter by minimum/maximum THC percentage

## Project Structure

```
terpene-sorter/
├── backend/
│   ├── app.py              # Flask API server
│   ├── scraper.py          # Web scraping logic
│   ├── requirements.txt    # Python dependencies
│   └── data/
│       └── products.json   # Cached product data
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ProductList.jsx
│   │   │   ├── ProductCard.jsx
│   │   │   ├── TerpeneFilter.jsx
│   │   │   └── TerpeneSorter.jsx
│   │   └── index.jsx
│   ├── package.json
│   └── index.html
└── README.md
```

## Terpenes Tracked

- Myrcene
- Limonene
- Caryophyllene
- Pinene (alpha & beta)
- Linalool
- Humulene
- Camphene
- Terpinolene
- Ocimene
- And more...
