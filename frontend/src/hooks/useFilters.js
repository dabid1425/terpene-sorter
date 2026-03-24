import { useState } from 'react'

export function useFilters() {
  const [selectedTerpenes, setSelectedTerpenes] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedStrainType, setSelectedStrainType] = useState('')
  const [minThc, setMinThc] = useState('')
  const [maxThc, setMaxThc] = useState('')
  const [hideMissingTerpenes, setHideMissingTerpenes] = useState(false)
  const [purchaseType, setPurchaseType] = useState('Recreational')

  const [sortBy, setSortBy] = useState('total_terpenes')
  const [sortOrder, setSortOrder] = useState('desc')
  const [terpenePriority, setTerpenePriority] = useState([])

  const handleTerpeneChange = (terpene) => {
    setSelectedTerpenes((prev) =>
      prev.includes(terpene) ? prev.filter((t) => t !== terpene) : [...prev, terpene]
    )
  }

  const addTerpenePriority = (terpene) => {
    if (!terpenePriority.includes(terpene)) {
      setTerpenePriority((prev) => [...prev, terpene])
    }
  }

  const removeTerpenePriority = (terpene) => {
    setTerpenePriority((prev) => prev.filter((t) => t !== terpene))
  }

  const moveTerpenePriority = (index, direction) => {
    setTerpenePriority((prev) => {
      const next = [...prev]
      const swapIndex = index + direction
      if (swapIndex < 0 || swapIndex >= next.length) return next
      ;[next[index], next[swapIndex]] = [next[swapIndex], next[index]]
      return next
    })
  }

  const clearFilters = () => {
    setSelectedTerpenes([])
    setSelectedCategory('')
    setSelectedStrainType('')
    setMinThc('')
    setMaxThc('')
    setSortBy('total_terpenes')
    setSortOrder('desc')
    setTerpenePriority([])
    setHideMissingTerpenes(false)
    setPurchaseType('Recreational')
  }

  return {
    selectedTerpenes,
    selectedCategory, setSelectedCategory,
    selectedStrainType, setSelectedStrainType,
    minThc, setMinThc,
    maxThc, setMaxThc,
    hideMissingTerpenes, setHideMissingTerpenes,
    purchaseType, setPurchaseType,
    sortBy, setSortBy,
    sortOrder, setSortOrder,
    terpenePriority,
    handleTerpeneChange,
    addTerpenePriority,
    removeTerpenePriority,
    moveTerpenePriority,
    clearFilters,
  }
}
