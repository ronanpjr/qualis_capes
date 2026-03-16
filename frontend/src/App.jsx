import { useState, useEffect } from 'react'
import './index.css'
import { useQualisData } from './hooks/useQualisData.js'
import AreaSelector from './components/AreaSelector.jsx'
import ClassificationFilter from './components/ClassificationFilter.jsx'
import ResultsTable from './components/ResultsTable.jsx'
import DistributionPanel from './components/DistributionPanel.jsx'
import ChatPanel from './components/ChatPanel.jsx'

const PER_PAGE = 20

export default function App() {
  const {
    areas, areasLoading,
    results, resultsLoading, resultsError,
    distribution, distLoading,
    fetchResults, fetchDistribution
  } = useQualisData(PER_PAGE)

  // --- Selected area & filters ---
  const [selectedArea, setSelectedArea] = useState(null)
  const [selectedEstratos, setSelectedEstratos] = useState([])
  const [searchText, setSearchText] = useState('')
  const [searchInput, setSearchInput] = useState('') // local input state
  const [currentPage, setCurrentPage] = useState(1)

  // React to area selection — resets all filters and fetches fresh data
  useEffect(() => {
    setSelectedEstratos([])
    setSearchText('')
    setSearchInput('')
    setCurrentPage(1)
    fetchDistribution(selectedArea)
    fetchResults(selectedArea, [], '', 1)
  }, [selectedArea, fetchDistribution, fetchResults])

  // NOTE: filter/page changes are handled directly in the event handlers below
  // (no second useEffect) to avoid double-firing when area changes.

  function handleAreaSelect(area) {
    setSelectedArea(area)
  }

  function handleEstratoChange(estratos) {
    setSelectedEstratos(estratos)
    setCurrentPage(1)
    fetchResults(selectedArea, estratos, searchText, 1)
  }

  function handleSearchSubmit(e) {
    e.preventDefault()
    setSearchText(searchInput)
    setCurrentPage(1)
    fetchResults(selectedArea, selectedEstratos, searchInput, 1)
  }

  function handlePageChange(page) {
    setCurrentPage(page)
    fetchResults(selectedArea, selectedEstratos, searchText, page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const hasContent = !!selectedArea

  return (
    <>
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">
            QUALIS CAPES
            <span>Consulta de Classificação de Periódicos</span>
          </div>
          <span className="header-badge">171.111 registros · 50 áreas</span>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="main-content">
        <div className="app-container">

          {/* Area selector */}
          <div className="card area-section">
            <AreaSelector
              areas={areas}
              selected={selectedArea}
              onSelect={handleAreaSelect}
              loading={areasLoading}
            />
          </div>

          {/* Content panel — only after area is selected */}
          {!hasContent ? (
            <div className="card" style={{ padding: '64px 24px' }}>
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <p>Selecione uma área de avaliação para começar</p>
                <small>Dados das classificações publicadas no Sucupira / CAPES</small>
              </div>
            </div>
          ) : (
            <div className="content-grid">
              {/* ── Left: Distribution ── */}
              <DistributionPanel
                data={distribution}
                loading={distLoading}
                area={selectedArea}
              />

              {/* ── Right: Filters + Table ── */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

                {/* Filters card */}
                <div className="card" style={{ padding: '20px' }}>
                  <ClassificationFilter
                    selected={selectedEstratos}
                    onChange={handleEstratoChange}
                  />

                  <div style={{ marginTop: '16px' }}>
                    <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px' }}>
                      <input
                        type="text"
                        value={searchInput}
                        onChange={e => setSearchInput(e.target.value)}
                        placeholder="Buscar por título ou ISSN…"
                        maxLength={200}
                      />
                      <button
                        type="submit"
                        className="btn-primary"
                        style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
                      >
                        Buscar
                      </button>
                      {searchText && (
                        <button
                          type="button"
                          onClick={() => { setSearchInput(''); setSearchText(''); setCurrentPage(1) }}
                          style={{
                            background: 'var(--neutral-50)',
                            border: '1px solid var(--neutral-200)',
                            borderRadius: '6px',
                            padding: '0 12px',
                            color: 'var(--neutral-700)',
                            fontSize: '13px',
                            flexShrink: 0,
                          }}
                        >
                          Limpar
                        </button>
                      )}
                    </form>
                  </div>

                  {/* Active filters summary */}
                  {(selectedEstratos.length > 0 || searchText) && (
                    <div style={{
                      marginTop: '12px',
                      paddingTop: '12px',
                      borderTop: '1px solid var(--neutral-200)',
                      fontSize: '12px',
                      color: 'var(--neutral-700)',
                    }}>
                      Filtrando por:
                      {selectedEstratos.length > 0 && (
                        <span style={{ marginLeft: '6px' }}>
                          estratos <strong>{selectedEstratos.join(', ')}</strong>
                        </span>
                      )}
                      {searchText && (
                        <span style={{ marginLeft: '6px' }}>
                          · busca <strong>"{searchText}"</strong>
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Error */}
                {resultsError && (
                  <div className="error-message">
                    Erro ao buscar dados: {resultsError}
                  </div>
                )}

                {/* Results table card */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ marginBottom: '12px' }}>
                    <h2 className="section-title" style={{ marginBottom: 0 }}>{selectedArea}</h2>
                  </div>
                  <ResultsTable
                    items={results?.items}
                    total={results?.total ?? 0}
                    page={currentPage}
                    perPage={PER_PAGE}
                    totalPages={results?.total_pages ?? 1}
                    loading={resultsLoading}
                    onPageChange={handlePageChange}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer style={{
        marginTop: '48px',
        padding: '24px',
        borderTop: '1px solid var(--neutral-200)',
        background: 'var(--white)',
        textAlign: 'center',
        fontSize: '12px',
        color: 'var(--neutral-400)',
      }}>
        Dados: QUALIS CAPES — Classificações Publicadas no Sucupira
      </footer>

      {/* ── Chatbot ── */}
      <ChatPanel />
    </>
  )
}
