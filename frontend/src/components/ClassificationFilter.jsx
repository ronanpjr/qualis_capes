const ESTRATOS = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C']

export default function ClassificationFilter({ selected, onChange }) {
  function toggle(estrato) {
    if (selected.includes(estrato)) {
      onChange(selected.filter(e => e !== estrato))
    } else {
      onChange([...selected, estrato])
    }
  }

  function clearAll() {
    onChange([])
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <p className="section-subtitle" style={{ marginBottom: 0 }}>Filtrar por Estrato</p>
        {selected.length > 0 && (
          <button
            onClick={clearAll}
            style={{
              background: 'none',
              color: 'var(--primary-500)',
              fontSize: '12px',
              fontWeight: 500,
              padding: '2px 6px',
            }}
          >
            Limpar
          </button>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        {ESTRATOS.map(estrato => {
          const isActive = selected.includes(estrato)
          return (
            <button
              key={estrato}
              onClick={() => toggle(estrato)}
              className={isActive ? `badge badge-${estrato}` : ''}
              style={{
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '11px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                border: isActive ? 'none' : '1px solid var(--neutral-200)',
                background: isActive ? undefined : 'var(--white)',
                color: isActive ? undefined : 'var(--neutral-700)',
              }}
            >
              {estrato}
            </button>
          )
        })}
      </div>
    </div>
  )
}
