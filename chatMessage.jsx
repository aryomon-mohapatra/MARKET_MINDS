import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { TrendingUp, User } from 'lucide-react'
import StockChart from './StockChart'
import ThinkingSteps from './ThinkingSteps'

function Avatar({ role }) {
  if (role === 'user') {
    return (
      <div style={{
        width: 30, height: 30, borderRadius: '50%',
        background: 'var(--bg3)',
        border: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <User size={15} color="var(--text2)" />
      </div>
    )
  }
  return (
    <div style={{
      width: 30, height: 30, borderRadius: 8,
      background: 'var(--accent)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <TrendingUp size={15} color="#fff" />
    </div>
  )
}

export default function ChatMessage({ message, thinkingSteps, isCurrentlyStreaming }) {
  const isUser      = message.role === 'user'
  const isStreaming = message.streaming
  const showThinking = !isUser && (thinkingSteps?.length > 0 || isCurrentlyStreaming)

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        gap: '0.75rem',
        padding: '1rem 0',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <Avatar role={message.role} />

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.78rem', color: 'var(--text3)', marginBottom: '0.4rem', fontWeight: 600 }}>
          {isUser ? 'You' : 'MarketMind'}
        </div>

        {/* Thinking steps (only for assistant while streaming) */}
        {showThinking && (
          <ThinkingSteps steps={thinkingSteps || []} isStreaming={isCurrentlyStreaming && !message.content} />
        )}

        {/* Message content */}
        {isUser ? (
          <div style={{ lineHeight: 1.65, fontSize: '0.9rem' }}>{message.content}</div>
        ) : (
          <div className="prose" style={{ fontSize: '0.9rem' }}>
            {message.content ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content + (isStreaming ? '▋' : '')}
              </ReactMarkdown>
            ) : isStreaming ? (
              <span style={{ color: 'var(--text3)' }}>
                <span className="dot-1">●</span>{' '}
                <span className="dot-2">●</span>{' '}
                <span className="dot-3">●</span>
              </span>
            ) : null}
          </div>
        )}

        {/* Inline charts */}
        {!isUser && message.chartData?.map((cd, i) => (
          <StockChart key={i} symbol={cd.symbol} period={cd.period} candles={cd.candles} />
        ))}
      </div>
    </div>
  )
}
