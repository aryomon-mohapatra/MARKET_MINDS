import {
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine
} from 'recharts'

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function formatPrice(v) {
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload || {}
  const change = d.close - d.open
  const changePct = ((change / d.open) * 100).toFixed(2)
  const isGreen = change >= 0

  return (
    <div style={{
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '0.6rem 0.9rem',
      fontSize: '0.78rem',
      minWidth: 160,
    }}>
      <div style={{ color: 'var(--text2)', marginBottom: 4 }}>{formatDate(label)}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 12px' }}>
        <span style={{ color: 'var(--text3)' }}>Open</span>  <span>{formatPrice(d.open)}</span>
        <span style={{ color: 'var(--text3)' }}>High</span>  <span style={{ color: 'var(--green)' }}>{formatPrice(d.high)}</span>
        <span style={{ color: 'var(--text3)' }}>Low</span>   <span style={{ color: 'var(--red)' }}>{formatPrice(d.low)}</span>
        <span style={{ color: 'var(--text3)' }}>Close</span> <span style={{ color: isGreen ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>{formatPrice(d.close)}</span>
      </div>
      <div style={{ marginTop: 4, color: isGreen ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
        {isGreen ? '▲' : '▼'} {Math.abs(changePct)}%
      </div>
    </div>
  )
}

export default function StockChart({ symbol, period, candles }) {
  if (!candles?.length) return null

  const data = candles.map(c => ({ ...c, color: c.close >= c.open ? '#10b981' : '#ef4444' }))
  const firstClose = data[0]?.close
  const lastClose  = data[data.length - 1]?.close
  const totalChg   = lastClose && firstClose ? ((lastClose - firstClose) / firstClose * 100) : 0
  const isPositive = totalChg >= 0

  // Thin the x-axis labels (show ~6)
  const step = Math.max(1, Math.floor(data.length / 6))
  const ticks = data.filter((_, i) => i % step === 0).map(d => d.date)

  return (
    <div style={{
      background: 'var(--bg3)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '1rem',
      marginTop: '0.75rem',
    }}>
      {/* Chart header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div>
          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{symbol}</span>
          <span style={{ color: 'var(--text3)', fontSize: '0.78rem', marginLeft: 8 }}>{period}</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1rem', fontWeight: 700 }}>{formatPrice(lastClose)}</div>
          <div style={{ fontSize: '0.78rem', color: isPositive ? 'var(--green)' : 'var(--red)' }}>
            {isPositive ? '▲' : '▼'} {Math.abs(totalChg).toFixed(2)}% ({period})
          </div>
        </div>
      </div>

      {/* Price line chart */}
      <ResponsiveContainer width="100%" height={180}>
        <ComposedChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`grad-${symbol}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={isPositive ? '#10b981' : '#ef4444'} stopOpacity={0.15} />
              <stop offset="100%" stopColor={isPositive ? '#10b981' : '#ef4444'} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            ticks={ticks}
            tickFormatter={formatDate}
            tick={{ fontSize: 10, fill: 'var(--text3)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={v => `₹${(v/1000).toFixed(0)}k`}
            tick={{ fontSize: 10, fill: 'var(--text3)' }}
            axisLine={false}
            tickLine={false}
            width={46}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={firstClose} stroke="rgba(255,255,255,0.1)" strokeDasharray="4 4" />
          <Line
            type="monotone"
            dataKey="close"
            stroke={isPositive ? '#10b981' : '#ef4444'}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume bar chart */}
      <ResponsiveContainer width="100%" height={50}>
        <ComposedChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Bar dataKey="volume" fill="rgba(99,102,241,0.25)" radius={[2, 2, 0, 0]} />
        </ComposedChart>
      </ResponsiveContainer>
      <div style={{ fontSize: '0.7rem', color: 'var(--text3)', textAlign: 'right', marginTop: 2 }}>
        Volume
      </div>
    </div>
  )
}
