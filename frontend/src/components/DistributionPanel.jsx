const ESTRATO_ORDER = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C']

export default function DistributionPanel({ data, loading, area }) {
  if (loading) {
    return (
      <div className="card" style={{ padding: '24px' }}>
        <div className="loading-spinner" style={{ padding: '32px' }}>
          <div className="spinner" />
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="card" style={{ padding: '24px' }}>
        <p className="section-subtitle">Distribuição por Estrato</p>
        <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--neutral-400)', fontSize: '13px' }}>
          Selecione uma área para ver a distribuição
        </div>
      </div>
    )
  }

  const countMap = Object.fromEntries(data.map(d => [d.estrato, d.count]))
  const total = data.reduce((s, d) => s + d.count, 0)
  const max = Math.max(...data.map(d => d.count))

  return (
    <div className="card" style={{ padding: '20px' }}>
      <p className="section-subtitle">Distribuição por Estrato</p>
      <div style={{ fontSize: '11px', color: 'var(--neutral-400)', marginBottom: '16px' }}>
        {total.toLocaleString('pt-BR')} periódicos no total
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {ESTRATO_ORDER.filter(e => countMap[e] !== undefined).map(estrato => {
          const count = countMap[estrato] || 0
          const pct = max > 0 ? (count / max) * 100 : 0
          const totalPct = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0'

          return (
            <div key={estrato}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '4px',
              }}>
                <span className={`badge badge-${estrato}`}>{estrato}</span>
                <span style={{ fontSize: '12px', color: 'var(--neutral-700)', fontWeight: 500 }}>
                  {count.toLocaleString('pt-BR')}
                  <span style={{ color: 'var(--neutral-400)', fontWeight: 400, marginLeft: '4px' }}>
                    ({totalPct}%)
                  </span>
                </span>
              </div>
              <div style={{
                height: '6px',
                background: 'var(--neutral-200)',
                borderRadius: '3px',
                overflow: 'hidden',
              }}>
                <div
                  style={{
                    height: '100%',
                    width: `${pct}%`,
                    borderRadius: '3px',
                    background: getBarColor(estrato),
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function getBarColor(estrato) {
  const map = {
    A1: '#166534', A2: '#15803D',
    A3: '#3B82F6', A4: '#6366F1',
    B1: '#CA8A04', B2: '#D97706',
    B3: '#EA580C', B4: '#DC2626',
    C:  '#9CA3AF',
  }
  return map[estrato] || 'var(--primary-500)'
}
