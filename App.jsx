import { useState, useRef, useEffect } from 'react'
import Header         from './components/Header'
import ChatMessage    from './components/ChatMessage'
import ChatInput      from './components/ChatInput'
import PortfolioPanel from './components/PortfolioPanel'
import WelcomeScreen  from './components/WelcomeScreen'
import { useChat }    from './hooks/useChat'
import { uploadPortfolio } from './api/client'

export default function App() {
  const [portfolio,      setPortfolio]      = useState(null)
  const [portfolioError, setPortfolioError] = useState(null)
  const [showPortfolio,  setShowPortfolio]  = useState(false)
  const messagesEndRef = useRef(null)

  const { messages, isStreaming, thinkingSteps, error, sendMessage, clearChat } = useChat(portfolio)

  // Auto-scroll to bottom as messages stream in
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleUpload = async (file) => {
    setPortfolioError(null)
    try {
      const result = await uploadPortfolio(file)
      setPortfolio(result)
      setShowPortfolio(true)
    } catch (e) {
      setPortfolioError(`Portfolio upload failed: ${e.message}`)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header
        onClear={clearChat}
        hasPortfolio={!!portfolio}
        portfolioValue={portfolio?.total_value || 0}
      />

      {/* Main content area */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Chat column */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Messages or welcome */}
          {messages.length === 0 ? (
            <WelcomeScreen onUpload={handleUpload} />
          ) : (
            <div style={{
              flex:      1,
              overflowY: 'auto',
              padding:   '0 1.5rem',
            }}>
              {messages.map((msg, i) => {
                const isLast          = i === messages.length - 1
                const isAssistant     = msg.role === 'assistant'
                const showThinking    = isLast && isAssistant && isStreaming
                const stepsForMsg     = showThinking ? thinkingSteps : msg.savedThinkingSteps || []

                return (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    thinkingSteps={stepsForMsg}
                    isCurrentlyStreaming={showThinking}
                  />
                )
              })}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Error bar */}
          {(error || portfolioError) && (
            <div style={{
              background: 'rgba(239,68,68,0.1)',
              border:     '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8,
              margin:     '0 1.5rem 0.5rem',
              padding:    '0.5rem 0.85rem',
              fontSize:   '0.78rem',
              color:      'var(--red)',
            }}>
              ⚠ {error || portfolioError}
            </div>
          )}

          <ChatInput
            onSend={sendMessage}
            onUpload={handleUpload}
            isStreaming={isStreaming}
            hasPortfolio={!!portfolio}
          />
        </div>

        {/* Portfolio sidebar */}
        {showPortfolio && portfolio && (
          <PortfolioPanel
            portfolio={portfolio}
            onClose={() => setShowPortfolio(false)}
          />
        )}
      </div>
    </div>
  )
}
