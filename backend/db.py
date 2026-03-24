"""
PostgreSQL data layer for Terpene Sorter.
Handles connection, schema initialisation, upserts, and loading.
"""

import json
import os

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/terpene_sorter")
# Normalise legacy Heroku "postgres://" prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create the products table if it doesn't exist yet."""
    ddl = """
    CREATE TABLE IF NOT EXISTS products (
        variant_id      INTEGER PRIMARY KEY,
        name            TEXT           NOT NULL,
        brand           TEXT           NOT NULL DEFAULT '',
        category        TEXT           NOT NULL DEFAULT '',
        strain_type     TEXT           NOT NULL DEFAULT '',
        price           NUMERIC(10,2)  NOT NULL DEFAULT 0,
        sale_price      NUMERIC(10,2)  NOT NULL DEFAULT 0,
        weight          TEXT           NOT NULL DEFAULT '',
        thc             NUMERIC(8,3)   NOT NULL DEFAULT 0,
        cbd             NUMERIC(8,3)   NOT NULL DEFAULT 0,
        image           TEXT           NOT NULL DEFAULT '',
        url             TEXT           NOT NULL DEFAULT '',
        terpenes        JSONB          NOT NULL DEFAULT '{}',
        total_terpenes  NUMERIC(8,4)   NOT NULL DEFAULT 0,
        purchase_type   TEXT           NOT NULL DEFAULT '',
        updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.execute("""
                ALTER TABLE products
                ADD COLUMN IF NOT EXISTS purchase_type TEXT NOT NULL DEFAULT '';
            """)
        conn.commit()


def save_products(products):
    """Bulk-upsert products into the database.

    Rows without both ``name`` and ``variant_id`` are skipped.
    """
    valid = [p for p in products if p.get("name") and p.get("variant_id")]
    if not valid:
        print("save_products: no valid rows to upsert (need name + variant_id)")
        return

    rows = [
        (
            p["variant_id"],
            p["name"],
            p.get("brand", ""),
            p.get("category", ""),
            p.get("strain_type", ""),
            p.get("price", 0) or 0,
            p.get("sale_price", 0) or 0,
            p.get("weight", ""),
            p.get("thc", 0) or 0,
            p.get("cbd", 0) or 0,
            p.get("image", ""),
            p.get("url", ""),
            json.dumps(p.get("terpenes") or {}),
            p.get("total_terpenes", 0) or 0,
            p.get("purchase_type", ""),
        )
        for p in valid
    ]

    sql = """
    INSERT INTO products (
        variant_id, name, brand, category, strain_type,
        price, sale_price, weight, thc, cbd,
        image, url, terpenes, total_terpenes, purchase_type
    ) VALUES %s
    ON CONFLICT (variant_id) DO UPDATE SET
        name           = EXCLUDED.name,
        brand          = EXCLUDED.brand,
        category       = EXCLUDED.category,
        strain_type    = EXCLUDED.strain_type,
        price          = EXCLUDED.price,
        sale_price     = EXCLUDED.sale_price,
        weight         = EXCLUDED.weight,
        thc            = EXCLUDED.thc,
        cbd            = EXCLUDED.cbd,
        image          = EXCLUDED.image,
        url            = EXCLUDED.url,
        terpenes       = EXCLUDED.terpenes,
        total_terpenes = EXCLUDED.total_terpenes,
        purchase_type  = EXCLUDED.purchase_type,
        updated_at     = NOW()
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
        conn.commit()

    print(f"Upserted {len(valid)} products into PostgreSQL ({len(products) - len(valid)} skipped)")


def load_products():
    """Return all products from the database as a list of plain dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        variant_id,
                        name,
                        brand,
                        category,
                        strain_type,
                        CAST(price          AS FLOAT) AS price,
                        CAST(sale_price     AS FLOAT) AS sale_price,
                        weight,
                        CAST(thc            AS FLOAT) AS thc,
                        CAST(cbd            AS FLOAT) AS cbd,
                        image,
                        url,
                        terpenes,
                        CAST(total_terpenes AS FLOAT) AS total_terpenes,
                        purchase_type
                    FROM products
                """)
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"load_products error: {e}")
        return []
