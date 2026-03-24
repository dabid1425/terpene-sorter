import React, { useState } from 'react'

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
  prioritySection: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #eee',
  },
  priorityTitle: {
    fontSize: '0.85rem',
    fontWeight: '600',
    color: '#555',
    marginBottom: '8px',
  },
  priorityAdd: {
    display: 'flex',
    gap: '6px',
    marginBottom: '10px',
  },
  prioritySelect: {
    flex: 1,
    padding: '7px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    fontSize: '0.85rem',
    backgroundColor: 'white',
    cursor: 'pointer',
  },
  addButton: {
    padding: '7px 12px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: '#2e7d32',
    color: 'white',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '600',
  },
  priorityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  priorityItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    backgroundColor: '#e8f5e9',
    borderRadius: '6px',
    padding: '6px 8px',
    fontSize: '0.85rem',
  },
  priorityRank: {
    width: '18px',
    textAlign: 'center',
    fontWeight: '700',
    color: '#2e7d32',
    fontSize: '0.8rem',
    flexShrink: 0,
  },
  priorityName: {
    flex: 1,
    textTransform: 'capitalize',
    color: '#333',
  },
  arrowButton: {
    padding: '2px 6px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.75rem',
    lineHeight: 1,
  },
  arrowButtonDisabled: {
    opacity: 0.3,
    cursor: 'default',
  },
  removeButton: {
    padding: '2px 6px',
    borderRadius: '4px',
    border: 'none',
    backgroundColor: '#ffcdd2',
    color: '#c62828',
    cursor: 'pointer',
    fontSize: '0.75rem',
    fontWeight: '700',
    lineHeight: 1,
  },
  activeNote: {
    fontSize: '0.75rem',
    color: '#2e7d32',
    fontStyle: 'italic',
    marginTop: '6px',
  },
}

function TerpeneSorter({
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
  availableTerpenes,
  terpenePriority,
  onAddTerpenePriority,
  onRemoveTerpenePriority,
  onMoveTerpenePriority,
}) {
  const [selectedToAdd, setSelectedToAdd] = useState('')

  const sortOptions = [
    { value: 'total_terpenes', label: 'Total Terpenes' },
    { value: 'thc', label: 'THC %' },
    { value: 'thc_mg', label: 'THC mg' },
    { value: 'cbd', label: 'CBD %' },
    { value: 'price', label: 'Price' },
    { value: 'name', label: 'Name' },
  ]

  const terpeneOptions = availableTerpenes.map((t) => ({
    value: t,
    label: t.charAt(0).toUpperCase() + t.slice(1),
  }))

  const unpickedTerpenes = availableTerpenes.filter((t) => !terpenePriority.includes(t))

  const handleAdd = () => {
    if (selectedToAdd) {
      onAddTerpenePriority(selectedToAdd)
      setSelectedToAdd('')
    }
  }

  return (
    <div style={styles.section}>
      <h3 style={styles.sectionTitle}>Sort Products</h3>

      <select
        style={{
          ...styles.select,
          opacity: terpenePriority.length > 0 ? 0.5 : 1,
        }}
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        disabled={terpenePriority.length > 0}
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

      <div style={{ ...styles.orderToggle, opacity: terpenePriority.length > 0 ? 0.5 : 1 }}>
        <button
          style={{
            ...styles.orderButton,
            ...(sortOrder === 'desc' ? styles.orderButtonActive : {}),
          }}
          onClick={() => setSortOrder('desc')}
          disabled={terpenePriority.length > 0}
        >
          {sortBy === 'name' ? 'Z-A' : 'High to Low'}
        </button>
        <button
          style={{
            ...styles.orderButton,
            ...(sortOrder === 'asc' ? styles.orderButtonActive : {}),
          }}
          onClick={() => setSortOrder('asc')}
          disabled={terpenePriority.length > 0}
        >
          {sortBy === 'name' ? 'A-Z' : 'Low to High'}
        </button>
      </div>

      {/* Multi-terpene priority sort */}
      <div style={styles.prioritySection}>
        <div style={styles.priorityTitle}>Priority Terpene Sort</div>

        <div style={styles.priorityAdd}>
          <select
            style={styles.prioritySelect}
            value={selectedToAdd}
            onChange={(e) => setSelectedToAdd(e.target.value)}
          >
            <option value="">Add terpene...</option>
            {unpickedTerpenes.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
          <button style={styles.addButton} onClick={handleAdd} disabled={!selectedToAdd}>
            +
          </button>
        </div>

        {terpenePriority.length > 0 && (
          <>
            <div style={styles.priorityList}>
              {terpenePriority.map((terpene, i) => (
                <div key={terpene} style={styles.priorityItem}>
                  <span style={styles.priorityRank}>{i + 1}</span>
                  <span style={styles.priorityName}>{terpene}</span>
                  <button
                    style={{
                      ...styles.arrowButton,
                      ...(i === 0 ? styles.arrowButtonDisabled : {}),
                    }}
                    onClick={() => onMoveTerpenePriority(i, -1)}
                    disabled={i === 0}
                  >
                    ▲
                  </button>
                  <button
                    style={{
                      ...styles.arrowButton,
                      ...(i === terpenePriority.length - 1 ? styles.arrowButtonDisabled : {}),
                    }}
                    onClick={() => onMoveTerpenePriority(i, 1)}
                    disabled={i === terpenePriority.length - 1}
                  >
                    ▼
                  </button>
                  <button
                    style={styles.removeButton}
                    onClick={() => onRemoveTerpenePriority(terpene)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <div style={styles.activeNote}>Priority sort active — overrides sort above</div>
          </>
        )}
      </div>
    </div>
  )
}

export default TerpeneSorter
