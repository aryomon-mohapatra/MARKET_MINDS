import { X, TrendingUp, TrendingDown, PieChart } from 'lucide-react'

function fmt(n) {
  if (!n) return '—'
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)}Cr`
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`
  return `₹${Number(n).toLocaleString('en-IN')}`
}

export default function PortfolioPanel({ portfolio, onClose }) {
  if (!portfolio) return null

  const { total_invested, total_value, gain_pct, holdings = [] } = portfolio
  const isGain = (gain_pct || 0) >= 0

  return (
    <div style={{
      width:       300,
      borderLeft:  '1px solid var(--border)',
      background:  'var(--bg2)',
      display:     'flex',
      flexDirection: 'column',
      flexShrink:  0,
      overflowY:   'auto',
    }}>
      {/* Header */}
      <div style={{
        padding:     '0.85rem 1rem',
        borderBottom:'1px solid var(--border)',
        display:     'flex',
        alignItems:  'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <PieChart size={14} color="var(--accent2)" />
          <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>Your Portfolio</span>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}>
          <X size={15} />
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ padding: '0.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{
          background:   'var(--bg3)',
          borderRadius: 10,
          padding:      '0.75rem',
          display:      'grid',
          gridTemplateColumns: '1fr 1fr',
          gap:          '0.5rem 1rem',
        }}>
          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text3)', marginBottom: 2 }}>Invested</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{fmt(total_invested)}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text3)', marginBottom: 2 }}>Current</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{fmt(total_value)}</div>
          </div>
          <div style={{ gridColumn: '1/-1' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text3)', marginBottom: 2 }}>Overall P&L</div>
            <div style={{
              fontWeight: 700, fontSize: '1rem',
              color: isGain ? 'var(--green)' : 'var(--red)',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              {isGain ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {fmt(total_value - total_invested)} ({(gain_pct || 0).toFixed(1)}%)
            </div>
          </div>
        </div>

        {/* Holdings list */}
        <div style={{ fontWeight: 600, fontSize: '0.78rem', color: 'var(--text3)', marginTop: '0.25rem' }}>
          HOLDINGS ({holdings.length})
        </div>

        {holdings.slice(0, 12).map((h, i) => {
          const cv   = h.current_value || 0
          const iv   = h.invested_value || 0
          const gain = cv - iv
          const gPct = iv ? (gain / iv * 100) : 0
          const wt   = total_value ? (cv / total_value * 100) : 0

          return (
            <div key={i} style={{
              background:   'var(--bg3)',
              borderRadius: 8,
              padding:      '0.6rem 0.75rem',
            }}>
              <div style={{
                display:        'flex',
                justifyContent: 'space-between',
                alignItems:     'flex-start',
                gap:            8,
              }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 500, lineHeight: 1.3, flex: 1 }}>
                  {h.fund_name?.replace(/\s*-\s*Direct\s*/i, ' ·')?.substring(0, 42)}
                </div>
                <div style={{
                  fontSize: '0.72rem',
                  color:    gPct >= 0 ? 'var(--green)' : 'var(--red)',
                  fontWeight: 600,
                  flexShrink: 0,
                }}>
                  {gPct >= 0 ? '+' : ''}{gPct.toFixed(1)}%
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text3)' }}>{fmt(cv)}</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text3)' }}>{wt.toFixed(1)}% of portfolio</span>
              </div>

              {/* Weight bar */}
              <div style={{ height: 3, background: 'var(--bg)', borderRadius: 2, marginTop: 5 }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(wt * 3, 100)}%`,
                  background: gPct >= 0 ? 'var(--green)' : 'var(--red)',
                  borderRadius: 2,
                  opacity: 0.6,
                }} />
              </div>
            </div>
          )
        })}

        {holdings.length > 12 && (
          <div style={{ fontSize: '0.73rem', color: 'var(--text3)', textAlign: 'center', padding: '0.25rem 0' }}>
            +{holdings.length - 12} more holdings
          </div>
        )}
      </div>
    </div>
  )
}
