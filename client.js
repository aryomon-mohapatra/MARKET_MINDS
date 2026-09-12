const BASE = import.meta.env.VITE_API_URL || '/api'

/**
 * Stream a chat query via SSE.
 * Calls onChunk(chunk) for every parsed SSE event.
 * Returns when the stream closes.
 */
export async function streamChat({ query, conversationHistory, portfolioContext, onChunk }) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      conversation_history: conversationHistory,
      portfolio_context:    portfolioContext || null,
    }),
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }

  const reader  = res.body.getReader()
  const decoder = new TextDecoder()
  let   buffer  = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()   // keep incomplete last line

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const raw = line.slice(6).trim()
      if (!raw) continue
      try {
        onChunk(JSON.parse(raw))
      } catch { /* skip malformed */ }
    }
  }
}

/** Upload CAMS/KFintech CSV and get back portfolio summary */
export async function uploadPortfolio(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/portfolio/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json()
}

/** Quick headline fetch for sidebar */
export async function fetchHeadlines(category = 'markets') {
  const res = await fetch(`${BASE}/market/headlines?category=${category}&limit=8`)
  if (!res.ok) return []
  const data = await res.json()
  return data.headlines || []
}
