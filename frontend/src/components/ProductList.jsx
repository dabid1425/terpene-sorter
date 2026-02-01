import React from 'react'
import ProductCard from './ProductCard'

const styles = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '20px',
  },
  empty: {
    textAlign: 'center',
    padding: '50px',
    color: '#666',
    fontSize: '1.1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
  },
}

function ProductList({ products }) {
  if (!products || products.length === 0) {
    return (
      <div style={styles.empty}>
        <p>No products found.</p>
        <p style={{ marginTop: '10px', fontSize: '0.9rem' }}>
          Try adjusting your filters or click "Refresh Data" to scrape new products.
        </p>
      </div>
    )
  }

  return (
    <div style={styles.grid}>
      {products.map((product, index) => (
        <ProductCard key={product.url || index} product={product} />
      ))}
    </div>
  )
}

export default ProductList
