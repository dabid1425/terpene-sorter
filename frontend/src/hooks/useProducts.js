import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api'

export function useProducts({ sortBy, sortOrder, selectedCategory, selectedStrainType, selectedTerpenes, minThc, maxThc, purchaseType }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [availableTerpenes, setAvailableTerpenes] = useState([])
  const [categories, setCategories] = useState([])
  const [strainTypes, setStrainTypes] = useState([])

  const fetchProducts = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      params.append('sort_by', sortBy === 'thc_mg' ? 'thc' : sortBy)
      params.append('sort_order', sortOrder)
      if (selectedCategory) params.append('category', selectedCategory)
      if (selectedStrainType) params.append('strain_type', selectedStrainType)
      if (selectedTerpenes.length > 0) params.append('terpenes', selectedTerpenes.join(','))
      if (minThc) params.append('min_thc', minThc)
      if (maxThc) params.append('max_thc', maxThc)
      if (purchaseType === 'Recreational') params.append('purchase_type', 'Recreational')

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
  }, [sortBy, sortOrder, selectedCategory, selectedStrainType, selectedTerpenes, minThc, maxThc, purchaseType])

  const fetchMetadata = useCallback(async () => {
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
  }, [])

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
  }, [fetchProducts, fetchMetadata])

  return { products, loading, refreshing, error, availableTerpenes, categories, strainTypes, refreshData }
}
