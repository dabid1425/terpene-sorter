import React, { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ProductList from './components/ProductList'
import { useProducts } from './hooks/useProducts'
import { useFilters } from './hooks/useFilters'

const MG_CATEGORIES = ['Edibles', 'Beverages', 'Topicals']
const PERCENT_CATEGORIES = ['Flower', 'Vapes', 'Concentrates', 'Pre-Rolls', 'Infused Pre-Rolls']
const PAGE_SIZES = [25, 50, 75, 100, 150, 200, 'All']

const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2e7d32',
    color: 'white',
    padding: '20px',
    textAlign: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  headerTitle: {
    fontSize: '2rem',
    marginBottom: '5px',
  },
  headerSubtitle: {
    fontSize: '1rem',
    opacity: 0.9,
  },
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '20px',
    display: 'grid',
    gridTemplateColumns: '280px 1fr',
    gap: '20px',
  },
  main: {
    minHeight: '500px',
  },
  loading: {
    textAlign: 'center',
    padding: '50px',
    fontSize: '1.2rem',
    color: '#666',
  },
}

function App() {
  const filters = useFilters()

  const {
    products, loading, refreshing, error,
    availableTerpenes, categories, strainTypes,
    refreshData,
  } = useProducts({
    sortBy: filters.sortBy,
    sortOrder: filters.sortOrder,
    selectedCategory: filters.selectedCategory,
    selectedStrainType: filters.selectedStrainType,
    selectedTerpenes: filters.selectedTerpenes,
    minThc: filters.minThc,
    maxThc: filters.maxThc,
    purchaseType: filters.purchaseType,
  })

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)

  const isTerpeneSort =
    filters.terpenePriority.length > 0 ||
    filters.sortBy === 'total_terpenes' ||
    availableTerpenes.includes(filters.sortBy)

  const sortedProducts = (() => {
    let base = products

    if (isTerpeneSort) {
      base = base.filter((p) => p.terpenes && Object.keys(p.terpenes).length > 0)
    }

    if (filters.hideMissingTerpenes) {
      base = base.filter((p) => !p.terpenes || Object.keys(p.terpenes).length === 0)
    }

    if (filters.sortBy === 'thc') {
      base = base.filter((p) => PERCENT_CATEGORIES.includes(p.category))
    } else if (filters.sortBy === 'thc_mg') {
      base = base
        .filter((p) => MG_CATEGORIES.includes(p.category))
        .sort((a, b) => filters.sortOrder === 'desc' ? b.thc - a.thc : a.thc - b.thc)
    }

    if (filters.terpenePriority.length > 0) {
      return [...base].sort((a, b) => {
        for (const terpene of filters.terpenePriority) {
          const aVal = a.terpenes?.[terpene] ?? 0
          const bVal = b.terpenes?.[terpene] ?? 0
          if (bVal !== aVal) return bVal - aVal
        }
        return 0
      })
    }

    return base
  })()

  const totalPages = pageSize === 'All' ? 1 : Math.ceil(sortedProducts.length / pageSize)
  const paginatedProducts =
    pageSize === 'All'
      ? sortedProducts
      : sortedProducts.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  const productsWithTerpenes = sortedProducts.filter(
    (p) => p.terpenes && Object.keys(p.terpenes).length > 0
  )

  // Reset to page 1 when results change
  useEffect(() => {
    setCurrentPage(1)
  }, [sortedProducts.length, filters.sortBy, filters.sortOrder, filters.purchaseType])

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>Terpene Sorter</h1>
        <p style={styles.headerSubtitle}>Browse and sort cannabis products by terpene profile</p>
      </header>

      <div style={styles.container}>
        <Sidebar
          refreshing={refreshing}
          onRefresh={refreshData}
          error={error}
          totalProducts={sortedProducts.length}
          totalWithTerpenes={productsWithTerpenes.length}
          sortBy={filters.sortBy} setSortBy={filters.setSortBy}
          sortOrder={filters.sortOrder} setSortOrder={filters.setSortOrder}
          availableTerpenes={availableTerpenes}
          terpenePriority={filters.terpenePriority}
          onAddTerpenePriority={filters.addTerpenePriority}
          onRemoveTerpenePriority={filters.removeTerpenePriority}
          onMoveTerpenePriority={filters.moveTerpenePriority}
          selectedTerpenes={filters.selectedTerpenes}
          onTerpeneChange={filters.handleTerpeneChange}
          categories={categories}
          selectedCategory={filters.selectedCategory}
          onCategoryChange={filters.setSelectedCategory}
          strainTypes={strainTypes}
          selectedStrainType={filters.selectedStrainType}
          onStrainTypeChange={filters.setSelectedStrainType}
          minThc={filters.minThc} onMinThcChange={filters.setMinThc}
          maxThc={filters.maxThc} onMaxThcChange={filters.setMaxThc}
          hideMissingTerpenes={filters.hideMissingTerpenes}
          onHideMissingTerpenesChange={filters.setHideMissingTerpenes}
          purchaseType={filters.purchaseType}
          onPurchaseTypeChange={filters.setPurchaseType}
          onClearFilters={filters.clearFilters}
        />

        <main style={styles.main}>
          {loading ? (
            <div style={styles.loading}>Loading products...</div>
          ) : (
            <ProductList
              products={paginatedProducts}
              currentPage={currentPage}
              totalPages={totalPages}
              pageSize={pageSize}
              pageSizes={PAGE_SIZES}
              totalCount={sortedProducts.length}
              onPageChange={setCurrentPage}
              onPageSizeChange={(size) => { setPageSize(size); setCurrentPage(1) }}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
