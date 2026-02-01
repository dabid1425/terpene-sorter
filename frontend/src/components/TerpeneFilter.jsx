import React from 'react'

const styles = {
  section: {
    marginBottom: '20px',
  },
  sectionTitle: {
    fontSize: '0.9rem',
    fontWeight: '600',
    color: '#333',
    marginBottom: '10px',
    paddingBottom: '5px',
    borderBottom: '2px solid #e8f5e9',
  },
  checkboxList: {
    maxHeight: '200px',
    overflowY: 'auto',
  },
  checkboxItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '5px 0',
    cursor: 'pointer',
  },
  checkbox: {
    marginRight: '8px',
    cursor: 'pointer',
  },
  label: {
    fontSize: '0.9rem',
    textTransform: 'capitalize',
    cursor: 'pointer',
  },
  select: {
    width: '100%',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    fontSize: '0.9rem',
    backgroundColor: 'white',
    cursor: 'pointer',
  },
  inputGroup: {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
  },
  input: {
    flex: 1,
    padding: '8px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    fontSize: '0.9rem',
  },
  inputLabel: {
    fontSize: '0.75rem',
    color: '#666',
    marginBottom: '4px',
  },
  clearButton: {
    width: '100%',
    padding: '10px',
    backgroundColor: '#f5f5f5',
    color: '#666',
    border: '1px solid #ddd',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    marginTop: '15px',
  },
  selectedCount: {
    fontSize: '0.75rem',
    color: '#2e7d32',
    marginLeft: '5px',
  },
}

function TerpeneFilter({
  availableTerpenes,
  selectedTerpenes,
  onTerpeneChange,
  categories,
  selectedCategory,
  onCategoryChange,
  strainTypes,
  selectedStrainType,
  onStrainTypeChange,
  minThc,
  maxThc,
  onMinThcChange,
  onMaxThcChange,
  onClearFilters,
}) {
  const hasActiveFilters =
    selectedTerpenes.length > 0 ||
    selectedCategory ||
    selectedStrainType ||
    minThc ||
    maxThc

  return (
    <div>
      {/* Category Filter */}
      {categories.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Category</h3>
          <select
            style={styles.select}
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Strain Type Filter */}
      {strainTypes.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Strain Type</h3>
          <select
            style={styles.select}
            value={selectedStrainType}
            onChange={(e) => onStrainTypeChange(e.target.value)}
          >
            <option value="">All Strain Types</option>
            {strainTypes.map((strainType) => (
              <option key={strainType} value={strainType}>
                {strainType}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* THC Range Filter */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>THC Range (%)</h3>
        <div style={styles.inputGroup}>
          <div style={{ flex: 1 }}>
            <div style={styles.inputLabel}>Min</div>
            <input
              type="number"
              style={styles.input}
              placeholder="0"
              value={minThc}
              onChange={(e) => onMinThcChange(e.target.value)}
              min="0"
              max="100"
            />
          </div>
          <div style={{ flex: 1 }}>
            <div style={styles.inputLabel}>Max</div>
            <input
              type="number"
              style={styles.input}
              placeholder="100"
              value={maxThc}
              onChange={(e) => onMaxThcChange(e.target.value)}
              min="0"
              max="100"
            />
          </div>
        </div>
      </div>

      {/* Terpene Filter */}
      {availableTerpenes.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>
            Filter by Terpenes
            {selectedTerpenes.length > 0 && (
              <span style={styles.selectedCount}>({selectedTerpenes.length} selected)</span>
            )}
          </h3>
          <p style={{ fontSize: '0.75rem', color: '#666', marginBottom: '10px' }}>
            Products must contain all selected terpenes
          </p>
          <div style={styles.checkboxList}>
            {availableTerpenes.map((terpene) => (
              <label key={terpene} style={styles.checkboxItem}>
                <input
                  type="checkbox"
                  style={styles.checkbox}
                  checked={selectedTerpenes.includes(terpene)}
                  onChange={() => onTerpeneChange(terpene)}
                />
                <span style={styles.label}>{terpene}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {hasActiveFilters && (
        <button style={styles.clearButton} onClick={onClearFilters}>
          Clear All Filters
        </button>
      )}
    </div>
  )
}

export default TerpeneFilter
