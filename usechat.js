import { useState, useCallback, useRef } from 'react'
import { streamChat } from '../api/client'

/**
 * Manages all chat state:
 *   messages, streaming, thinking steps, chart data, errors
 */
export function useChat(portfolioContext) {
  const [messages,       setMessages]       = useState([])
  const [isStreaming,    setIsStreaming]     = useState(false)
  const [thinkingSteps,  setThinkingSteps]  = useState([])
  const [error,          setError]          = useState(null)
  const abortRef = useRef(false)

  const sendMessage = useCallback(async (query) => {
    if (!query.trim() || isStreaming) return

    setError(null)
    abortRef.current = false

    // Add user message immediately
    const userMsg = { role: 'user', content: query, id: Date.now() }
    setMessages(prev => [...prev, userMsg])

    // Placeholder assistant message we'll fill in as chunks arrive
    const assistantId = Date.now() + 1
    const assistantMsg = {
      role:         'assistant',
      content:      '',
      id:           assistantId,
      thinkingSteps:[],
      chartData:    [],
      streaming:    true,
    }
    setMessages(prev => [...prev, assistantMsg])
    setIsStreaming(true)
    setThinkingSteps([])

    try {
      // Build history (all prior messages except the one we just added)
      const history = messages.map(m => ({ role: m.role, content: m.content }))

      await streamChat({
        query,
        conversationHistory: history,
        portfolioContext,
        onChunk: (chunk) => {
          if (abortRef.current) return

          if (chunk.type === 'thinking') {
            setThinkingSteps(prev => [...prev, { type: 'thinking', content: chunk.content }])
          }

          else if (chunk.type === 'agent_call') {
            setThinkingSteps(prev => [...prev, {
              type:  'agent_call',
              agent: chunk.agent,
              input: chunk.input,
            }])
          }

          else if (chunk.type === 'agent_result') {
            setThinkingSteps(prev => {
              const updated = [...prev]
              // Attach result to the last agent_call for that agent
              const idx = [...updated].reverse().findIndex(
                s => s.type === 'agent_call' && s.agent === chunk.agent
              )
              if (idx !== -1) {
                const realIdx = updated.length - 1 - idx
                updated[realIdx] = { ...updated[realIdx], result: chunk.summary }
              }
              return updated
            })
          }

          else if (chunk.type === 'stream') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId
                ? { ...m, content: m.content + chunk.content }
                : m
            ))
          }

          else if (chunk.type === 'chart_data') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId
                ? { ...m, chartData: [...(m.chartData || []), chunk] }
                : m
            ))
          }

          else if (chunk.type === 'done') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId ? { ...m, streaming: false } : m
            ))
            setIsStreaming(false)
            setThinkingSteps([])
          }

          else if (chunk.type === 'error') {
            setError(chunk.message)
            setMessages(prev => prev.map(m =>
              m.id === assistantId
                ? { ...m, content: `⚠ ${chunk.message}`, streaming: false }
                : m
            ))
            setIsStreaming(false)
            setThinkingSteps([])
          }
        },
      })
    } catch (err) {
      setError(err.message)
      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? { ...m, content: `⚠ Error: ${err.message}`, streaming: false }
          : m
      ))
      setIsStreaming(false)
      setThinkingSteps([])
    }
  }, [messages, isStreaming, portfolioContext])

  const clearChat = useCallback(() => {
    setMessages([])
    setThinkingSteps([])
    setError(null)
  }, [])

  return { messages, isStreaming, thinkingSteps, error, sendMessage, clearChat }
}
