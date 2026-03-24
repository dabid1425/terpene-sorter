import React from 'react'
import TerpeneSorter from './TerpeneSorter'
import TerpeneFilter from './TerpeneFilter'

const styles = {
  sidebar: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    position: 'sticky',
    top: '20px',
    maxHeight: 'calc(100vh - 40px)',
    overflowY: 'auto',
  },
  refreshButton: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#2e7d32',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '1rem',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
  },
  refreshButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  stats: {
    backgroundColor: '#e8f5e9',
    padding: '15px',
    borderRadius: '6px',
    marginBottom: '20px',
    fontSize: '0.9rem',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '15px',
    borderRadius: '6px',
    marginBottom: '20px',
  },
}

function Sidebar({
  refreshing,
  onRefresh,
  error,
  totalProducts,
  totalWithTerpenes,
  sortBy, setSortBy,
  sortOrder, setSortOrder,
  availableTerpenes,
  terpenePriority,
  onAddTerpenePriority,
  onRemoveTerpenePriority,
  onMoveTerpenePriority,
  selectedTerpenes,
  onTerpeneChange,
  categories,
  selectedCategory,
  onCategoryChange,
  strainTypes,
  selectedStrainType,
  onStrainTypeChange,
  minThc, onMinThcChange,
  maxThc, onMaxThcChange,
  hideMissingTerpenes,
  onHideMissingTerpenesChange,
  purchaseType,
  onPurchaseTypeChange,
  onClearFilters,
}) {
  return (
    <aside style={styles.sidebar}>
      <button
        style={{ ...styles.refreshButton, ...(refreshing ? styles.refreshButtonDisabled : {}) }}
        onClick={onRefresh}
        disabled={refreshing}
      >
        {refreshing ? 'Refreshing...' : 'Refresh Data'}
      </button>

      <div style={styles.stats}>
        <strong>Products:</strong> {totalProducts}
        <br />
        <strong>With Terpenes:</strong> {totalWithTerpenes}
      </div>

      {error && <div style={styles.error}>{error}</div>}

      <TerpeneSorter
        sortBy={sortBy}
        setSortBy={setSortBy}
        sortOrder={sortOrder}
        setSortOrder={setSortOrder}
        availableTerpenes={availableTerpenes}
        terpenePriority={terpenePriority}
        onAddTerpenePriority={onAddTerpenePriority}
        onRemoveTerpenePriority={onRemoveTerpenePriority}
        onMoveTerpenePriority={onMoveTerpenePriority}
      />

      <TerpeneFilter
        availableTerpenes={availableTerpenes}
        selectedTerpenes={selectedTerpenes}
        onTerpeneChange={onTerpeneChange}
        categories={categories}
        selectedCategory={selectedCategory}
        onCategoryChange={onCategoryChange}
        strainTypes={strainTypes}
        selectedStrainType={selectedStrainType}
        onStrainTypeChange={onStrainTypeChange}
        minThc={minThc}
        maxThc={maxThc}
        onMinThcChange={onMinThcChange}
        onMaxThcChange={onMaxThcChange}
        hideMissingTerpenes={hideMissingTerpenes}
        onHideMissingTerpenesChange={onHideMissingTerpenesChange}
        purchaseType={purchaseType}
        onPurchaseTypeChange={onPurchaseTypeChange}
        onClearFilters={onClearFilters}
      />
    </aside>
  )
}

export default Sidebar
