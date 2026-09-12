import { TrendingUp, RefreshCw } from 'lucide-react'

export default function Header({ onClear, hasPortfolio, portfolioValue }) {
  return (
    <header style={{
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'space-between',
      padding:        '0 1.5rem',
      height:         '56px',
      borderBottom:   '1px solid var(--border)',
      background:     'var(--bg2)',
      flexShrink:      0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <div style={{
          width: 32, height: 32,
          background: 'var(--accent)',
          borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <TrendingUp size={18} color="#fff" />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', lineHeight: 1 }}>
            MarketMind
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text3)', letterSpacing: '0.05em' }}>
            NEXT GEN · ET AI HACKATHON 2026
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {hasPortfolio && (
          <div style={{
            background: 'rgba(99,102,241,0.12)',
            border:     '1px solid rgba(99,102,241,0.3)',
            borderRadius: 20,
            padding:    '0.25rem 0.75rem',
            fontSize:   '0.78rem',
            color:      'var(--accent2)',
          }}>
            📊 Portfolio ₹{(portfolioValue / 100000).toFixed(1)}L
          </div>
        )}
        <button
          onClick={onClear}
          title="New conversation"
          style={{
            background: 'transparent',
            border:     '1px solid var(--border)',
            borderRadius: 8,
            padding:    '0.35rem 0.75rem',
            color:      'var(--text2)',
            cursor:     'pointer',
            fontSize:   '0.8rem',
            display:    'flex', alignItems: 'center', gap: '0.4rem',
          }}>
          <RefreshCw size={13} />
          New chat
        </button>
      </div>
    </header>
  )
}
