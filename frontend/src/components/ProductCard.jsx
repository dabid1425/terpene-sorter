import React from 'react'

const styles = {
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    overflow: 'hidden',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  cardHover: {
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
  },
  imageContainer: {
    height: '200px',
    backgroundColor: '#e8f5e9',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  image: {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
  },
  placeholder: {
    color: '#aaa',
    fontSize: '3rem',
  },
  content: {
    padding: '15px',
  },
  name: {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginBottom: '8px',
    color: '#333',
    lineHeight: '1.3',
  },
  meta: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '12px',
  },
  badge: {
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: '500',
  },
  categoryBadge: {
    backgroundColor: '#e3f2fd',
    color: '#1565c0',
  },
  strainBadge: {
    backgroundColor: '#f3e5f5',
    color: '#7b1fa2',
  },
  priceBadge: {
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    fontWeight: '600',
  },
  cannabinoids: {
    display: 'flex',
    gap: '15px',
    marginBottom: '12px',
    padding: '10px',
    backgroundColor: '#fafafa',
    borderRadius: '6px',
  },
  cannabinoid: {
    textAlign: 'center',
  },
  cannabinoidLabel: {
    fontSize: '0.7rem',
    color: '#666',
    textTransform: 'uppercase',
  },
  cannabinoidValue: {
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#333',
  },
  terpeneSection: {
    borderTop: '1px solid #eee',
    paddingTop: '12px',
  },
  terpeneHeader: {
    fontSize: '0.85rem',
    fontWeight: '600',
    color: '#666',
    marginBottom: '8px',
    display: 'flex',
    justifyContent: 'space-between',
  },
  totalTerpenes: {
    color: '#2e7d32',
  },
  terpeneList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  terpene: {
    backgroundColor: '#e8f5e9',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '0.75rem',
  },
  terpeneName: {
    color: '#666',
    textTransform: 'capitalize',
  },
  terpeneValue: {
    color: '#2e7d32',
    fontWeight: '600',
    marginLeft: '4px',
  },
  noTerpenes: {
    color: '#999',
    fontSize: '0.85rem',
    fontStyle: 'italic',
  },
  link: {
    display: 'block',
    textAlign: 'center',
    marginTop: '12px',
    padding: '8px',
    backgroundColor: '#2e7d32',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '0.9rem',
  },
}

function ProductCard({ product }) {
  const [isHovered, setIsHovered] = React.useState(false)

  const terpenes = product.terpenes || {}
  const sortedTerpenes = Object.entries(terpenes)
    .filter(([_, value]) => value > 0)
    .sort((a, b) => b[1] - a[1])

  const totalTerpenes = product.total_terpenes || sortedTerpenes.reduce((sum, [_, v]) => sum + v, 0)

  return (
    <div
      style={{
        ...styles.card,
        ...(isHovered ? styles.cardHover : {}),
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div style={styles.imageContainer}>
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            style={styles.image}
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
        ) : (
          <span style={styles.placeholder}>🌿</span>
        )}
      </div>

      <div style={styles.content}>
        <h3 style={styles.name}>{product.name || 'Unknown Product'}</h3>

        <div style={styles.meta}>
          {product.category && (
            <span style={{ ...styles.badge, ...styles.categoryBadge }}>{product.category}</span>
          )}
          {product.strain_type && (
            <span style={{ ...styles.badge, ...styles.strainBadge }}>{product.strain_type}</span>
          )}
          {product.price > 0 && (
            <span style={{ ...styles.badge, ...styles.priceBadge }}>${product.price.toFixed(2)}</span>
          )}
          {product.brand && (
            <span style={styles.badge}>{product.brand}</span>
          )}
        </div>

        <div style={styles.cannabinoids}>
          <div style={styles.cannabinoid}>
            <div style={styles.cannabinoidLabel}>THC</div>
            <div style={styles.cannabinoidValue}>
              {product.thc ? `${product.thc.toFixed(1)}%` : '--'}
            </div>
          </div>
          <div style={styles.cannabinoid}>
            <div style={styles.cannabinoidLabel}>CBD</div>
            <div style={styles.cannabinoidValue}>
              {product.cbd ? `${product.cbd.toFixed(1)}%` : '--'}
            </div>
          </div>
          <div style={styles.cannabinoid}>
            <div style={styles.cannabinoidLabel}>Total Terps</div>
            <div style={{ ...styles.cannabinoidValue, ...styles.totalTerpenes }}>
              {totalTerpenes > 0 ? `${totalTerpenes.toFixed(2)}%` : '--'}
            </div>
          </div>
        </div>

        <div style={styles.terpeneSection}>
          <div style={styles.terpeneHeader}>
            <span>Terpene Profile</span>
          </div>
          {sortedTerpenes.length > 0 ? (
            <div style={styles.terpeneList}>
              {sortedTerpenes.slice(0, 6).map(([name, value]) => (
                <span key={name} style={styles.terpene}>
                  <span style={styles.terpeneName}>{name}:</span>
                  <span style={styles.terpeneValue}>{value.toFixed(2)}%</span>
                </span>
              ))}
              {sortedTerpenes.length > 6 && (
                <span style={styles.terpene}>+{sortedTerpenes.length - 6} more</span>
              )}
            </div>
          ) : (
            <p style={styles.noTerpenes}>No terpene data available</p>
          )}
        </div>

        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.link}
          >
            View Product
          </a>
        )}
      </div>
    </div>
  )
}

export default ProductCard
