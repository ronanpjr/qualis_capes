import { useState, useEffect, useCallback } from 'react'
import { getAreas, getPeriodicos, getDistribuicao } from '../api.js'

export function useQualisData(perPage = 20) {
  const [areas, setAreas] = useState([])
  const [areasLoading, setAreasLoading] = useState(true)

  const [results, setResults] = useState(null)
  const [resultsLoading, setResultsLoading] = useState(false)
  const [resultsError, setResultsError] = useState(null)

  const [distribution, setDistribution] = useState(null)
  const [distLoading, setDistLoading] = useState(false)

  useEffect(() => {
    getAreas()
      .then(data => setAreas(data))
      .catch(console.error)
      .finally(() => setAreasLoading(false))
  }, [])

  const fetchResults = useCallback(async (area, estratos, search, page) => {
    if (!area) {
      setResults(null)
      return
    }
    setResultsLoading(true)
    setResultsError(null)
    try {
      const data = await getPeriodicos({
        area,
        estrato: estratos.length > 0 ? estratos : undefined,
        search: search || undefined,
        page,
        per_page: perPage,
      })
      setResults(data)
    } catch (err) {
      setResultsError(err.message)
    } finally {
      setResultsLoading(false)
    }
  }, [perPage])

  const fetchDistribution = useCallback(async (area) => {
    if (!area) {
      setDistribution(null)
      return
    }
    setDistLoading(true)
    try {
      const data = await getDistribuicao(area)
      setDistribution(data.distribuicao ?? data)
    } catch (err) {
      console.error('Distribution error:', err)
    } finally {
      setDistLoading(false)
    }
  }, [])

  return {
    areas,
    areasLoading,
    results,
    resultsLoading,
    resultsError,
    distribution,
    distLoading,
    fetchResults,
    fetchDistribution
  }
}
