import { useState, useEffect, useRef } from 'react'

export default function AreaSelector({ areas, selected, onSelect, loading }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const filtered = areas.filter(a =>
    a.toLowerCase().includes(query.toLowerCase())
  )

  function handleSelect(area) {
    onSelect(area)
    setQuery('')
    setOpen(false)
  }

  return (
    <div style={{ position: 'relative' }} ref={ref}>
      <p className="section-subtitle">Área de Avaliação</p>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--white)',
          border: `1px solid ${open ? 'var(--primary-500)' : 'var(--neutral-400)'}`,
          borderRadius: '6px',
          padding: '0 12px',
          boxShadow: open ? '0 0 0 3px var(--primary-100)' : 'none',
          transition: 'border-color 0.15s, box-shadow 0.15s',
          cursor: 'pointer',
        }}
        onClick={() => !loading && setOpen(v => !v)}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--neutral-400)" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>

        <input
          type="text"
          value={open ? query : (selected || '')}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => setOpen(true)}
          placeholder={loading ? 'Carregando áreas…' : 'Selecionar área de avaliação…'}
          disabled={loading}
          style={{
            border: 'none',
            boxShadow: 'none',
            padding: '10px 0',
            flex: 1,
            fontSize: '14px',
            cursor: open ? 'text' : 'pointer',
            background: 'transparent',
          }}
          readOnly={!open}
        />

        {selected && !open && (
          <button
            onClick={e => { e.stopPropagation(); onSelect(null); setQuery('') }}
            style={{
              background: 'none',
              color: 'var(--neutral-400)',
              fontSize: '16px',
              padding: '4px',
              lineHeight: 1,
            }}
            title="Limpar seleção"
          >
            ×
          </button>
        )}

        <svg
          width="14" height="14" viewBox="0 0 24 24" fill="none"
          stroke="var(--neutral-400)" strokeWidth="2"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s', flexShrink: 0 }}
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </div>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0, right: 0,
            maxHeight: '300px',
            overflowY: 'auto',
            background: 'var(--white)',
            border: '1px solid var(--neutral-200)',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            zIndex: 200,
          }}
        >
          {filtered.length === 0 ? (
            <div style={{ padding: '16px', color: 'var(--neutral-400)', fontSize: '13px', textAlign: 'center' }}>
              Nenhuma área encontrada
            </div>
          ) : (
            filtered.map(area => (
              <div
                key={area}
                onClick={() => handleSelect(area)}
                style={{
                  padding: '10px 16px',
                  fontSize: '13px',
                  cursor: 'pointer',
                  background: area === selected ? 'var(--primary-100)' : 'transparent',
                  color: area === selected ? 'var(--primary-700)' : 'var(--neutral-900)',
                  fontWeight: area === selected ? 600 : 400,
                  transition: 'background 0.1s',
                  borderBottom: '1px solid var(--neutral-200)',
                }}
                onMouseEnter={e => { if (area !== selected) e.currentTarget.style.background = 'var(--neutral-50)' }}
                onMouseLeave={e => { if (area !== selected) e.currentTarget.style.background = 'transparent' }}
              >
                {area}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
