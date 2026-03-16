export default function ResultsTable({ items, total, page, perPage, totalPages, loading, onPageChange }) {
  if (loading) {
    return (
      <div className="animate-in">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '12px',
        }}>
          <div className="skeleton skeleton-text" style={{ width: '150px', margin: 0 }}></div>
          <div className="skeleton skeleton-text" style={{ width: '80px', margin: 0 }}></div>
        </div>

        <div style={{ overflowX: 'auto', border: '1px solid var(--neutral-200)', borderRadius: 'var(--radius-md)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: 'var(--primary-50)' }}>
                <th style={thStyle}>ISSN</th>
                <th style={{ ...thStyle, textAlign: 'left', width: '100%' }}>Título do Periódico</th>
                <th style={thStyle}>Estrato</th>
              </tr>
            </thead>
            <tbody>
              {[...Array(10)].map((_, idx) => (
                <tr key={`skeleton-${idx}`} style={{
                  background: idx % 2 === 0 ? 'var(--white)' : 'var(--neutral-50)',
                  borderBottom: '1px solid var(--neutral-200)',
                }}>
                  <td style={tdStyle}>
                    <div className="skeleton skeleton-text" style={{ width: '80px', margin: '0 auto' }}></div>
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'left' }}>
                    <div className="skeleton skeleton-text" style={{ width: '60%', margin: 0 }}></div>
                  </td>
                  <td style={tdStyle}>
                    <div className="skeleton skeleton-badge" style={{ margin: '0 auto' }}></div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  if (!items || items.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📄</div>
        <p>Nenhum periódico encontrado</p>
        <small>Tente ajustar os filtros ou a busca</small>
      </div>
    )
  }

  return (
    <div className="animate-in">
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px',
      }}>
        <span style={{ fontSize: '13px', color: 'var(--neutral-700)' }}>
          <strong style={{ color: 'var(--neutral-900)' }}>{total.toLocaleString('pt-BR')}</strong> periódicos encontrados
        </span>
        <span style={{ fontSize: '12px', color: 'var(--neutral-400)' }}>
          Página {page} de {totalPages}
        </span>
      </div>

      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--neutral-200)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--primary-50)' }}>
              <th style={thStyle}>ISSN</th>
              <th style={{ ...thStyle, textAlign: 'left', width: '100%' }}>Título do Periódico</th>
              <th style={thStyle}>Estrato</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr
                key={item.id}
                style={{
                  background: idx % 2 === 0 ? 'var(--white)' : 'var(--neutral-50)',
                  borderBottom: '1px solid var(--neutral-200)',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--primary-100)'}
                onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? 'var(--white)' : 'var(--neutral-50)'}
              >
                <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: '12px', whiteSpace: 'nowrap', color: 'var(--neutral-700)' }}>
                  {item.issn || '—'}
                </td>
                <td style={{ ...tdStyle, textAlign: 'left', color: 'var(--neutral-900)' }}>
                  {item.titulo}
                </td>
                <td style={tdStyle}>
                  <span className={`badge badge-${item.estrato}`}>{item.estrato}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          paddingTop: '20px',
        }}>
          <PageButton
            onClick={() => onPageChange(1)}
            disabled={page === 1}
            title="Primeira"
          >«</PageButton>

          <PageButton
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            title="Anterior"
          >‹</PageButton>

          {getPageNumbers(page, totalPages).map((p, i) =>
            p === '...' ? (
              <span key={`ellipsis-${i}`} style={{ padding: '0 4px', color: 'var(--neutral-400)' }}>…</span>
            ) : (
              <PageButton
                key={p}
                onClick={() => onPageChange(p)}
                active={p === page}
              >{p}</PageButton>
            )
          )}

          <PageButton
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            title="Próxima"
          >›</PageButton>

          <PageButton
            onClick={() => onPageChange(totalPages)}
            disabled={page === totalPages}
            title="Última"
          >»</PageButton>
        </div>
      )}
    </div>
  )
}

function PageButton({ onClick, disabled, active, children, title }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={{
        minWidth: '36px',
        height: '36px',
        padding: '0 8px',
        borderRadius: 'var(--radius-md)',
        fontFamily: 'var(--font-sans)',
        fontSize: '13px',
        fontWeight: active ? 600 : 500,
        background: active ? 'var(--primary-900)' : 'var(--white)',
        color: active ? 'var(--white)' : disabled ? 'var(--neutral-400)' : 'var(--neutral-700)',
        border: `1px solid ${active ? 'var(--primary-900)' : 'var(--neutral-200)'}`,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.2s',
        boxShadow: active ? 'var(--shadow-md)' : 'var(--shadow-sm)'
      }}
      onMouseEnter={e => {
        if (!disabled && !active) {
          e.currentTarget.style.background = 'var(--neutral-50)';
          e.currentTarget.style.borderColor = 'var(--neutral-400)';
        }
      }}
      onMouseLeave={e => {
        if (!disabled && !active) {
          e.currentTarget.style.background = 'var(--white)';
          e.currentTarget.style.borderColor = 'var(--neutral-200)';
        }
      }}
    >
      {children}
    </button>
  )
}

function getPageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  if (current <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total)
  } else if (current >= total - 3) {
    pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
  } else {
    pages.push(1, '...', current - 1, current, current + 1, '...', total)
  }
  return pages
}

const thStyle = {
  padding: '12px 16px',
  textAlign: 'center',
  fontWeight: 600,
  fontSize: '12px',
  color: 'var(--neutral-700)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  borderBottom: '2px solid var(--neutral-200)',
  whiteSpace: 'nowrap',
}

const tdStyle = {
  padding: '12px 16px',
  textAlign: 'center',
  verticalAlign: 'middle',
}
