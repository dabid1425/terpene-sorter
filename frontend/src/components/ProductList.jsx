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
  pagination: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: '24px',
    padding: '12px 16px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    flexWrap: 'wrap',
    gap: '12px',
  },
  pageInfo: {
    fontSize: '0.9rem',
    color: '#555',
  },
  pageControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  pageBtn: {
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.85rem',
  },
  pageBtnActive: {
    backgroundColor: '#2e7d32',
    color: 'white',
    borderColor: '#2e7d32',
  },
  pageBtnDisabled: {
    opacity: 0.4,
    cursor: 'default',
  },
  pageSizeSelect: {
    padding: '6px 10px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    fontSize: '0.85rem',
    backgroundColor: 'white',
    cursor: 'pointer',
  },
}

function getPageNumbers(currentPage, totalPages) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1)
  if (currentPage <= 4) return [1, 2, 3, 4, 5, '...', totalPages]
  if (currentPage >= totalPages - 3) return [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages]
  return [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages]
}

function ProductList({ products, currentPage, totalPages, pageSize, pageSizes, totalCount, onPageChange, onPageSizeChange }) {
  if (!products || totalCount === 0) {
    return (
      <div style={styles.empty}>
        <p>No products found.</p>
        <p style={{ marginTop: '10px', fontSize: '0.9rem' }}>
          Try adjusting your filters or click "Refresh Data" to scrape new products.
        </p>
      </div>
    )
  }

  const startItem = pageSize === 'All' ? 1 : (currentPage - 1) * pageSize + 1
  const endItem = pageSize === 'All' ? totalCount : Math.min(currentPage * pageSize, totalCount)

  return (
    <div>
      <div style={styles.grid}>
        {products.map((product, index) => (
          <ProductCard key={product.url || index} product={product} />
        ))}
      </div>

      <div style={styles.pagination}>
        <div style={styles.pageInfo}>
          Showing {startItem}–{endItem} of {totalCount} products
        </div>

        {pageSize !== 'All' && totalPages > 1 && (
          <div style={styles.pageControls}>
            <button
              style={{ ...styles.pageBtn, ...(currentPage === 1 ? styles.pageBtnDisabled : {}) }}
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              ‹
            </button>
            {getPageNumbers(currentPage, totalPages).map((page, i) =>
              page === '...' ? (
                <span key={`ellipsis-${i}`} style={{ padding: '0 4px', color: '#999' }}>…</span>
              ) : (
                <button
                  key={page}
                  style={{ ...styles.pageBtn, ...(page === currentPage ? styles.pageBtnActive : {}) }}
                  onClick={() => onPageChange(page)}
                >
                  {page}
                </button>
              )
            )}
            <button
              style={{ ...styles.pageBtn, ...(currentPage === totalPages ? styles.pageBtnDisabled : {}) }}
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              ›
            </button>
          </div>
        )}

        <select
          style={styles.pageSizeSelect}
          value={pageSize}
          onChange={(e) => onPageSizeChange(e.target.value === 'All' ? 'All' : Number(e.target.value))}
        >
          {pageSizes.map((size) => (
            <option key={size} value={size}>
              {size === 'All' ? 'Show All' : `${size} per page`}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

export default ProductList
