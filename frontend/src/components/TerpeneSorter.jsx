import React from 'react'

const styles = {
  section: {
    marginBottom: '20px',
    paddingBottom: '20px',
    borderBottom: '1px solid #eee',
  },
  sectionTitle: {
    fontSize: '0.9rem',
    fontWeight: '600',
    color: '#333',
    marginBottom: '10px',
    paddingBottom: '5px',
    borderBottom: '2px solid #e8f5e9',
  },
  select: {
    width: '100%',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    fontSize: '0.9rem',
    backgroundColor: 'white',
    cursor: 'pointer',
    marginBottom: '10px',
  },
  orderToggle: {
    display: 'flex',
    gap: '10px',
  },
  orderButton: {
    flex: 1,
    padding: '8px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.85rem',
    transition: 'all 0.2s',
  },
  orderButtonActive: {
    backgroundColor: '#2e7d32',
    color: 'white',
    borderColor: '#2e7d32',
  },
}

function TerpeneSorter({ sortBy, setSortBy, sortOrder, setSortOrder, availableTerpenes }) {
  const sortOptions = [
    { value: 'total_terpenes', label: 'Total Terpenes' },
    { value: 'thc', label: 'THC %' },
    { value: 'cbd', label: 'CBD %' },
    { value: 'price', label: 'Price' },
    { value: 'name', label: 'Name' },
  ]

  // Add individual terpenes as sort options
  const terpeneOptions = availableTerpenes.map((t) => ({
    value: t,
    label: t.charAt(0).toUpperCase() + t.slice(1),
  }))

  return (
    <div style={styles.section}>
      <h3 style={styles.sectionTitle}>Sort Products</h3>

      <select
        style={styles.select}
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
      >
        <optgroup label="General">
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </optgroup>
        {terpeneOptions.length > 0 && (
          <optgroup label="By Terpene">
            {terpeneOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </optgroup>
        )}
      </select>

      <div style={styles.orderToggle}>
        <button
          style={{
            ...styles.orderButton,
            ...(sortOrder === 'desc' ? styles.orderButtonActive : {}),
          }}
          onClick={() => setSortOrder('desc')}
        >
          {sortBy === 'name' ? 'Z-A' : 'High to Low'}
        </button>
        <button
          style={{
            ...styles.orderButton,
            ...(sortOrder === 'asc' ? styles.orderButtonActive : {}),
          }}
          onClick={() => setSortOrder('asc')}
        >
          {sortBy === 'name' ? 'A-Z' : 'Low to High'}
        </button>
      </div>
    </div>
  )
}

export default TerpeneSorter
