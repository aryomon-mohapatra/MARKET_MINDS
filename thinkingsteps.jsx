import { Brain, Database, Newspaper, BarChart2, PieChart, Globe } from 'lucide-react'

const AGENT_META = {
  get_stock_quote:              { icon: BarChart2,  label: 'Live prices',      color: '#6366f1' },
  get_price_history:            { icon: BarChart2,  label: 'Price history',    color: '#6366f1' },
  get_company_news_and_filings: { icon: Newspaper,  label: 'News + filings',   color: '#f59e0b' },
  get_technical_indicators:     { icon: Database,   label: 'Technicals',       color: '#10b981' },
  get_stock_fundamentals:       { icon: PieChart,   label: 'Fundamentals',     color: '#ec4899' },
  get_market_headlines:         { icon: Globe,      label: 'ET Headlines',     color: '#3b82f6' },
}

function AgentIcon({ agent, size = 14 }) {
  const meta  = AGENT_META[agent] || {}
  const Icon  = meta.icon || Database
  const color = meta.color || '#6b7280'
  return (
    <div style={{
      width:          24, height: 24,
      borderRadius:   6,
      background:     `${color}22`,
      border:         `1px solid ${color}44`,
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'center',
      flexShrink:     0,
    }}>
      <Icon size={size} color={color} />
    </div>
  )
}

export default function ThinkingSteps({ steps, isStreaming }) {
  if (!steps.length && !isStreaming) return null

  return (
    <div style={{
      margin:       '0 0 0.75rem',
      background:   'var(--bg3)',
      border:       '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow:     'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding:     '0.5rem 0.85rem',
        borderBottom:'1px solid var(--border)',
        display:     'flex',
        alignItems:  'center',
        gap:         '0.5rem',
        fontSize:    '0.75rem',
        color:       'var(--text3)',
      }}>
        <Brain size={12} color="var(--accent2)" />
        <span style={{ color: 'var(--accent2)', fontWeight: 600 }}>Reasoning</span>
        {isStreaming && (
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 3 }}>
            {[1,2,3].map(i => (
              <span key={i} className={`dot-${i}`} style={{
                width: 4, height: 4, borderRadius: '50%',
                background: 'var(--accent2)', display: 'inline-block',
              }} />
            ))}
          </span>
        )}
      </div>

      {/* Steps */}
      <div style={{ padding: '0.6rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {steps.map((step, i) => {
          if (step.type === 'thinking') {
            return (
              <div key={i} style={{
                fontSize: '0.78rem',
                color:    'var(--text3)',
                display:  'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}>
                <span style={{ color: 'var(--accent2)' }}>◆</span>
                {step.content}
              </div>
            )
          }

          if (step.type === 'agent_call') {
            const meta  = AGENT_META[step.agent] || {}
            const label = meta.label || step.agent
            const syms  = step.input?.symbols?.join(', ') || step.input?.symbol || step.input?.category || ''

            return (
              <div key={i} style={{
                display:    'flex',
                alignItems: 'flex-start',
                gap:        '0.5rem',
              }}>
                <AgentIcon agent={step.agent} />
                <div style={{ fontSize: '0.78rem' }}>
                  <span style={{ color: 'var(--text2)', fontWeight: 500 }}>{label}</span>
                  {syms && <span style={{ color: 'var(--text3)', marginLeft: 4 }}>→ {syms}</span>}
                  {step.result ? (
                    <div style={{ color: 'var(--text3)', marginTop: '0.15rem', fontSize: '0.73rem' }}>
                      ✓ {step.result}
                    </div>
                  ) : (
                    <div style={{ color: 'var(--text3)', marginTop: '0.15rem', fontSize: '0.73rem' }}>
                      Fetching…
                    </div>
                  )}
                </div>
              </div>
            )
          }

          return null
        })}
      </div>
    </div>
  )
}
