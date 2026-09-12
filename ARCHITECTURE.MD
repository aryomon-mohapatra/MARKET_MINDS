# MarketMind — Architecture Document
**ET AI Hackathon 2026 | Team Submission**

---

## Overview

MarketMind is a multi-agent AI system for Indian retail investors. It replaces static
chatbot responses with a live, multi-step reasoning pipeline that fetches real NSE/BSE data,
ET news, technical indicators, and BSE filings — then synthesizes a cited, portfolio-aware
answer using Claude claude-opus-4-5.

---

## Agent Roles

| Agent | Responsibility | Data Source |
|-------|---------------|-------------|
| **Orchestrator** | Reads user query, builds a reasoning plan, decides which agents to call, streams the synthesized response | Claude claude-opus-4-5 tool-use API |
| **Market Data Agent** | Live stock quotes, OHLCV history, fundamentals (P/E, P/B, EPS) | yfinance (NSE/BSE via Yahoo Finance) |
| **News & Filings Agent** | Latest ET headlines, company-specific news, BSE corporate filings | ET RSS feeds, BSE India API |
| **Technical Agent** | RSI-14, MACD, Bollinger Bands, SMA-20/50/200, support/resistance pivot points | pandas-ta on yfinance OHLCV |
| **Portfolio Agent** | Parses CAMS/KFintech CSV, computes portfolio weights, injects context into every query | User-uploaded CSV |

---

## How Agents Communicate

```
User Query
    │
    ▼
Orchestrator (Claude tool-use)
    │  Selects 1–4 tools based on query type
    ├──► Market Data Agent  ──► yfinance
    ├──► News Agent         ──► ET RSS + BSE API
    ├──► Technical Agent    ──► pandas-ta
    └──► Portfolio Agent    ──► CAMS CSV (in-memory)
    │
    ▼  All results returned as JSON
Response Synthesizer (Claude streaming)
    │  Portfolio context injected into system prompt
    │  Source citations enforced in prompt
    ▼
Streamed SSE response → React frontend
```

---

## Tool Integration

- **Claude tool-use API**: The orchestrator calls `client.messages.create()` with 6 tool definitions. Claude decides which tools to invoke based on the query. Results are passed back for synthesis.
- **SSE streaming**: The final synthesis uses `client.messages.stream()` so the frontend renders tokens in real time.
- **Portfolio injection**: When a CAMS CSV is uploaded, a plain-English portfolio context string (top 10 holdings, total value, P&L) is prepended to the Claude system prompt on every request.
- **Citation enforcement**: System prompt instructs Claude to always cite sources using `[Source: name]` inline.

---

## Error Handling

- All agent calls are wrapped in try/except; errors return `{"error": "..."}` without crashing the pipeline.
- The orchestrator continues with available data even if one agent fails.
- The frontend shows agent-level status in the "Reasoning" panel so users see exactly which data sources were hit.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM backbone | Groq llama-3.3-70b claude-opus-4-5 |
| Backend API | FastAPI + uvicorn (Python 3.11) |
| Market data | yfinance, pandas-ta |
| News | feedparser (ET RSS), BSE India REST API |
| Frontend | React 18 + Vite |
| Charts | Recharts (candlestick + volume) |
| Markdown | react-markdown + remark-gfm |

---

## Impact Model

**Baseline**: A retail investor spends ~20 minutes manually reading 4–6 ET articles + checking NSE website + calculating technicals to answer "Should I buy stock X?"

**With MarketMind**: Same answer in under 30 seconds, with live data, cited sources, and portfolio-aware risk flags.

| Metric | Estimate |
|--------|----------|
| Time saved per query | ~18 minutes |
| Queries per active user per week | ~5 |
| Time saved per user per week | ~90 minutes |
| TAM (ET Markets MAU ~20M) | Significant |
| Data freshness advantage over ET's existing Market ChatGPT | Real-time vs static |

**Key differentiators over ET's existing Market ChatGPT**:
1. Multi-step reasoning (3–5 data sources per answer, not 1)
2. Portfolio-awareness (knows what you hold)
3. Source citations on every factual claim
4. Live price + chart rendered inline
5. BSE filings integration (corporate announcements)
