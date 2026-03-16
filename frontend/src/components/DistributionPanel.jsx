import React, { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

const ESTRATO_ORDER = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C']

// Map estrato colors for the chart to match the new CSS variables
const ESTRATO_COLORS = {
  A1: 'var(--estrato-a1-chart)',
  A2: 'var(--estrato-a2-chart)',
  A3: 'var(--estrato-a3-chart)',
  A4: 'var(--estrato-a4-chart)',
  B1: 'var(--estrato-b1-chart)',
  B2: 'var(--estrato-b2-chart)',
  B3: 'var(--estrato-b3-chart)',
  B4: 'var(--estrato-b4-chart)',
  C:  'var(--estrato-c-chart)',
}

export default function DistributionPanel({ data, loading, area }) {
  const { chartData, total } = useMemo(() => {
    if (!data || data.length === 0) return { chartData: [], total: 0 }

    const countMap = Object.fromEntries(data.map(d => [d.estrato, d.count]))
    const totalCount = data.reduce((s, d) => s + d.count, 0)

    const formattedData = ESTRATO_ORDER
      .filter(e => countMap[e] !== undefined && countMap[e] > 0)
      .map(estrato => ({
        name: estrato,
        value: countMap[estrato],
        color: ESTRATO_COLORS[estrato] || '#3b82f6'
      }))

    return { chartData: formattedData, total: totalCount }
  }, [data])

  if (loading) {
    return (
      <div className="card" style={{ padding: '20px' }}>
        <p className="skeleton skeleton-title" style={{ width: '60%' }}></p>
        <p className="skeleton skeleton-text" style={{ width: '40%', marginBottom: '24px' }}></p>

        {/* Skeleton Chart */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '36px' }}>
          <div className="skeleton" style={{ width: '180px', height: '180px', borderRadius: '50%' }}></div>
        </div>

        {/* Skeleton Legend Items */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="skeleton" style={{ width: '12px', height: '12px', borderRadius: '50%' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '100%', margin: 0 }}></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="card" style={{ padding: '24px' }}>
        <p className="section-subtitle">Distribuição por Estrato</p>
        <div className="empty-state" style={{ padding: '48px 0' }}>
          <div className="empty-state-icon" style={{ color: 'var(--neutral-400)' }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 20V10M12 20V4M6 20v-4" />
            </svg>
          </div>
          <p>Selecione uma área para ver a distribuição</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card animate-in" style={{ padding: '20px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h3 className="section-subtitle" style={{ marginBottom: '4px', color: 'var(--neutral-900)' }}>
          Distribuição de Qualidade
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--neutral-400)' }}>
          {total.toLocaleString('pt-BR')} periódicos classificados
        </p>
      </div>

      <div style={{ width: '100%', height: '220px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              stroke="none"
              animationBegin={0}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip total={total} />} />
            <Legend content={<CustomLegend />} verticalAlign="bottom" height={36} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Custom Tooltip for Recharts
const CustomTooltip = ({ active, payload, total }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const percentage = ((data.value / total) * 100).toFixed(1)

    return (
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(4px)',
        border: '1px solid var(--neutral-200)',
        borderRadius: 'var(--radius-md)',
        padding: '12px',
        boxShadow: 'var(--shadow-lg)',
        minWidth: '140px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span className={`badge badge-${data.name}`}>{data.name}</span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--neutral-900)' }}>
            {percentage}%
          </span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--neutral-700)', margin: 0 }}>
          <strong>{data.value.toLocaleString('pt-BR')}</strong> periódicos
        </p>
      </div>
    )
  }
  return null
}

// Custom Legend to match our badging system perfectly
const CustomLegend = ({ payload }) => {
  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'center',
      gap: '8px',
      marginTop: '12px',
      paddingBottom: '16px'
    }}>
      {payload.map((entry, index) => (
        <div key={`item-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: entry.color }} />
          <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--neutral-700)' }}>
            {entry.payload.name}
          </span>
        </div>
      ))}
    </div>
  )
}

