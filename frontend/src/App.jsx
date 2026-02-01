import React, { useState, useEffect, useCallback } from 'react'
import ProductList from './components/ProductList'
import ProductCard from './components/ProductCard'
import TerpeneFilter from './components/TerpeneFilter'
import TerpeneSorter from './components/TerpeneSorter'

const API_BASE = '/api'

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
  sidebar: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    height: 'fit-content',
    position: 'sticky',
    top: '20px',
  },
  main: {
    minHeight: '500px',
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
  loading: {
    textAlign: 'center',
    padding: '50px',
    fontSize: '1.2rem',
    color: '#666',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '15px',
    borderRadius: '6px',
    marginBottom: '20px',
  },
}

function App() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  // Filter state
  const [selectedTerpenes, setSelectedTerpenes] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedStrainType, setSelectedStrainType] = useState('')
  const [minThc, setMinThc] = useState('')
  const [maxThc, setMaxThc] = useState('')

  // Sort state
  const [sortBy, setSortBy] = useState('total_terpenes')
  const [sortOrder, setSortOrder] = useState('desc')

  // Available options
  const [availableTerpenes, setAvailableTerpenes] = useState([])
  const [categories, setCategories] = useState([])
  const [strainTypes, setStrainTypes] = useState([])

  const fetchProducts = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      params.append('sort_by', sortBy)
      params.append('sort_order', sortOrder)

      if (selectedCategory) params.append('category', selectedCategory)
      if (selectedStrainType) params.append('strain_type', selectedStrainType)
      if (selectedTerpenes.length > 0) params.append('terpenes', selectedTerpenes.join(','))
      if (minThc) params.append('min_thc', minThc)
      if (maxThc) params.append('max_thc', maxThc)

      const response = await fetch(`${API_BASE}/products?${params}`)
      const data = await response.json()
      setProducts(data.products || [])
      setError(null)
    } catch (err) {
      setError('Failed to fetch products. Make sure the backend server is running.')
      console.error('Error fetching products:', err)
    } finally {
      setLoading(false)
    }
  }, [sortBy, sortOrder, selectedCategory, selectedStrainType, selectedTerpenes, minThc, maxThc])

  const fetchMetadata = async () => {
    try {
      const [terpeneRes, categoryRes, strainRes] = await Promise.all([
        fetch(`${API_BASE}/terpenes`),
        fetch(`${API_BASE}/categories`),
        fetch(`${API_BASE}/strain-types`),
      ])

      const terpeneData = await terpeneRes.json()
      const categoryData = await categoryRes.json()
      const strainData = await strainRes.json()

      setAvailableTerpenes(terpeneData.terpenes || [])
      setCategories(categoryData.categories || [])
      setStrainTypes(strainData.strain_types || [])
    } catch (err) {
      console.error('Error fetching metadata:', err)
    }
  }

  const refreshData = async () => {
    setRefreshing(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/refresh`, { method: 'POST' })
      const data = await response.json()
      if (data.success) {
        setProducts(data.products || [])
        await fetchMetadata()
      } else {
        setError(data.error || 'Failed to refresh data')
      }
    } catch (err) {
      setError('Failed to refresh data. Check console for details.')
      console.error('Error refreshing:', err)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchProducts()
    fetchMetadata()
  }, [fetchProducts])

  const handleTerpeneChange = (terpene) => {
    setSelectedTerpenes((prev) =>
      prev.includes(terpene) ? prev.filter((t) => t !== terpene) : [...prev, terpene]
    )
  }

  const clearFilters = () => {
    setSelectedTerpenes([])
    setSelectedCategory('')
    setSelectedStrainType('')
    setMinThc('')
    setMaxThc('')
    setSortBy('total_terpenes')
    setSortOrder('desc')
  }

  const productsWithTerpenes = products.filter(
    (p) => p.terpenes && Object.keys(p.terpenes).length > 0
  )

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>Terpene Sorter</h1>
        <p style={styles.headerSubtitle}>Browse and sort cannabis products by terpene profile</p>
      </header>

      <div style={styles.container}>
        <aside style={styles.sidebar}>
          <button
            style={{
              ...styles.refreshButton,
              ...(refreshing ? styles.refreshButtonDisabled : {}),
            }}
            onClick={refreshData}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh Data'}
          </button>

          <div style={styles.stats}>
            <strong>Products:</strong> {products.length}
            <br />
            <strong>With Terpenes:</strong> {productsWithTerpenes.length}
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <TerpeneSorter
            sortBy={sortBy}
            setSortBy={setSortBy}
            sortOrder={sortOrder}
            setSortOrder={setSortOrder}
            availableTerpenes={availableTerpenes}
          />

          <TerpeneFilter
            availableTerpenes={availableTerpenes}
            selectedTerpenes={selectedTerpenes}
            onTerpeneChange={handleTerpeneChange}
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            strainTypes={strainTypes}
            selectedStrainType={selectedStrainType}
            onStrainTypeChange={setSelectedStrainType}
            minThc={minThc}
            maxThc={maxThc}
            onMinThcChange={setMinThc}
            onMaxThcChange={setMaxThc}
            onClearFilters={clearFilters}
          />
        </aside>

        <main style={styles.main}>
          {loading ? (
            <div style={styles.loading}>Loading products...</div>
          ) : (
            <ProductList products={products} />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
