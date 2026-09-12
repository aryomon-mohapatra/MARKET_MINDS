import { useState, useRef } from 'react'
import { Send, Upload, Loader2 } from 'lucide-react'

const SUGGESTIONS = [
  "Should I buy Reliance at current levels?",
  "What's the technical outlook for HDFC Bank?",
  "Why is Adani Enterprises stock falling today?",
  "Compare TCS vs Infosys fundamentals",
  "What are today's top market movers on NSE?",
  "Analyse my portfolio for sector concentration risk",
]

export default function ChatInput({ onSend, onUpload, isStreaming, hasPortfolio }) {
  const [query,     setQuery]     = useState('')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef(null)

  const handleSend = () => {
    const q = query.trim()
    if (!q || isStreaming) return
    onSend(q)
    setQuery('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await onUpload(file)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div style={{
      borderTop:  '1px solid var(--border)',
      background: 'var(--bg2)',
      padding:    '1rem 1.5rem 1.25rem',
      flexShrink: 0,
    }}>
      {/* Suggestion chips (only shown when no messages) */}
      {!isStreaming && (
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          {SUGGESTIONS.slice(0, hasPortfolio ? 6 : 5).map((s, i) => (
            <button
              key={i}
              onClick={() => { setQuery(s); }}
              style={{
                background:   'var(--bg3)',
                border:       '1px solid var(--border)',
                borderRadius: 20,
                padding:      '0.3rem 0.75rem',
                fontSize:     '0.73rem',
                color:        'var(--text2)',
                cursor:       'pointer',
                whiteSpace:   'nowrap',
                transition:   'border-color 0.15s',
              }}
              onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
              onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
        {/* Upload button */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          title={hasPortfolio ? "Portfolio loaded ✓ — upload new" : "Upload CAMS/KFintech CSV"}
          style={{
            width:      40, height: 40,
            background: hasPortfolio ? 'rgba(99,102,241,0.15)' : 'var(--bg3)',
            border:     `1px solid ${hasPortfolio ? 'rgba(99,102,241,0.4)' : 'var(--border)'}`,
            borderRadius: 10,
            display:    'flex', alignItems: 'center', justifyContent: 'center',
            cursor:     uploading ? 'wait' : 'pointer',
            flexShrink: 0,
            color:      hasPortfolio ? 'var(--accent2)' : 'var(--text3)',
          }}>
          {uploading
            ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
            : <Upload size={16} />}
        </button>
        <input ref={fileRef} type="file" accept=".csv" onChange={handleFile} style={{ display: 'none' }} />

        {/* Text area */}
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder={isStreaming ? 'Analysing…' : 'Ask anything about Indian markets…'}
          disabled={isStreaming}
          rows={1}
          style={{
            flex:       1,
            background: 'var(--bg3)',
            border:     '1px solid var(--border)',
            borderRadius: 10,
            padding:    '0.6rem 0.9rem',
            color:      'var(--text)',
            fontSize:   '0.9rem',
            resize:     'none',
            outline:    'none',
            lineHeight: 1.5,
            maxHeight:  120,
            overflowY:  'auto',
            transition: 'border-color 0.15s',
          }}
          onFocus={e  => e.target.style.borderColor = 'var(--accent)'}
          onBlur={e   => e.target.style.borderColor = 'var(--border)'}
        />

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!query.trim() || isStreaming}
          style={{
            width:      40, height: 40,
            background: (!query.trim() || isStreaming) ? 'var(--bg3)' : 'var(--accent)',
            border:     'none',
            borderRadius: 10,
            display:    'flex', alignItems: 'center', justifyContent: 'center',
            cursor:     (!query.trim() || isStreaming) ? 'not-allowed' : 'pointer',
            flexShrink: 0,
            transition: 'background 0.15s',
          }}>
          <Send size={16} color={(!query.trim() || isStreaming) ? 'var(--text3)' : '#fff'} />
        </button>
      </div>

      <div style={{ fontSize: '0.68rem', color: 'var(--text3)', marginTop: '0.5rem', textAlign: 'center' }}>
        {hasPortfolio
          ? '📊 Portfolio-aware · All responses cite sources · Not SEBI-registered advice'
          : '📎 Upload your CAMS/KFintech CSV for portfolio-aware analysis · Not SEBI-registered advice'}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
