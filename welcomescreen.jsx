import { TrendingUp, BarChart2, Newspaper, PieChart, Upload } from 'lucide-react'

const FEATURES = [
  { icon: BarChart2,  color: '#6366f1', title: 'Live NSE/BSE data',     desc: 'Real-time prices, OHLCV, 52w range' },
  { icon: Newspaper,  color: '#f59e0b', title: 'ET News + BSE Filings', desc: 'Latest headlines and corporate announcements' },
  { icon: TrendingUp, color: '#10b981', title: 'Technical analysis',    desc: 'RSI, MACD, Bollinger, support/resistance' },
  { icon: PieChart,   color: '#ec4899', title: 'Portfolio-aware',       desc: 'Upload CAMS CSV for personalised answers' },
]

export default function WelcomeScreen({ onUpload }) {
  return (
    <div style={{
      flex:           1,
      display:        'flex',
      flexDirection:  'column',
      alignItems:     'center',
      justifyContent: 'center',
      padding:        '2rem',
      gap:            '2rem',
      overflowY:      'auto',
    }}>
      {/* Logo */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width:          64, height: 64,
          background:     'var(--accent)',
          borderRadius:   18,
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'center',
          margin:         '0 auto 1rem',
        }}>
          <TrendingUp size={32} color="#fff" />
        </div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem' }}>
          MarketMind <span style={{ color: 'var(--accent2)' }}>Next Gen</span>
        </h1>
        <p style={{ color: 'var(--text2)', fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
          India's most advanced AI analyst — live NSE/BSE data, ET news, technical analysis,
          and portfolio-aware insights. All cited. All real-time.
        </p>
      </div>

      {/* Feature grid */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap:                 '0.75rem',
        maxWidth:            480,
        width:               '100%',
      }}>
        {FEATURES.map(({ icon: Icon, color, title, desc }) => (
          <div key={title} style={{
            background:   'var(--bg2)',
            border:       '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            padding:      '0.85rem',
            display:      'flex',
            gap:          '0.6rem',
            alignItems:   'flex-start',
          }}>
            <div style={{
              width:          32, height: 32,
              borderRadius:   8,
              background:     `${color}22`,
              border:         `1px solid ${color}44`,
              display:        'flex',
              alignItems:     'center',
              justifyContent: 'center',
              flexShrink:     0,
            }}>
              <Icon size={15} color={color} />
            </div>
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.15rem' }}>{title}</div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text3)', lineHeight: 1.4 }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Upload CTA */}
      <div style={{
        background:   'rgba(99,102,241,0.08)',
        border:       '1px dashed rgba(99,102,241,0.35)',
        borderRadius: 'var(--radius)',
        padding:      '1rem 1.5rem',
        textAlign:    'center',
        maxWidth:     420,
        width:        '100%',
        cursor:       'pointer',
      }}
        onClick={() => document.getElementById('welcome-upload')?.click()}
      >
        <Upload size={20} color="var(--accent2)" style={{ marginBottom: 6 }} />
        <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--accent2)', marginBottom: 4 }}>
          Connect your portfolio (optional)
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text3)' }}>
          Upload your CAMS or KFintech statement CSV for personalised, portfolio-aware answers
        </div>
        <input id="welcome-upload" type="file" accept=".csv" style={{ display: 'none' }}
          onChange={e => { if (e.target.files?.[0]) onUpload(e.target.files[0]) }} />
      </div>

      <div style={{ fontSize: '0.72rem', color: 'var(--text3)', textAlign: 'center' }}>
        Built for ET AI Hackathon 2026 · Not SEBI-registered investment advice
      </div>
    </div>
  )
}
