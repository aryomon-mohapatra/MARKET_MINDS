# 📈 MarketMind

> **ET AI Hackathon 2026 | Problem Statement 6 — AI for the Indian Investor**

India has 14 crore+ demat accounts. Multi-agent AI analyst for NSE & BSE — built for ET AI Hackathon 2026.

**MarketMind** is a multi-agent AI system that doesn't just answer questions — it *researches* them. For every query, it autonomously fetches live NSE/BSE prices, ET news headlines, BSE corporate filings, and technical indicators, then synthesizes a cited, portfolio-aware answer using Claude claude-opus-4-5.

---

## 🎯 What Makes This Different

| ET's Existing Market ChatGPT | MarketMind |
|------------------------------|---------------------|
| Single-step response | 3–5 agent calls per query |
| Static knowledge | Live NSE/BSE data via yfinance |
| No citations | Every fact cited with source + URL |
| No portfolio awareness | Upload CAMS CSV → personalized answers |
| Text only | Inline candlestick charts + volume |
| No filings | BSE corporate announcements integrated |

---

## 🏗 Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│     Orchestrator (Claude tool-use)  │
│  Routes query → picks agents        │
└──────┬──────┬──────┬───────┬────────┘
       │      │      │       │
  Market   News   Tech  Portfolio
   Data   Agent  Agent   Agent
   Agent    │      │       │
   │      ET RSS  pandas  CAMS
 yfinance  BSE    -ta     CSV
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full detail.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free) → [console.groq.com](https://console.groq.com) — sign up and copy your key

### 1. Clone & backend setup

```bash
git clone https://github.com/YOUR_USERNAME/marketmind
cd marketmind/backend

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GROQ_API_KEY

uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### 2. Frontend setup

```bash
cd ../frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at http://localhost:3000

---

## 🔑 Environment Variables

**backend/.env**
```
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
MAX_TOKENS=4096
PORT=8000
```

**frontend/.env**
```
VITE_API_URL=/api
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat/stream` | Main SSE streaming chat endpoint |
| `POST` | `/portfolio/upload` | Upload CAMS/KFintech CSV |
| `GET`  | `/market/quote?symbols=RELIANCE,TCS` | Live quotes |
| `GET`  | `/market/ohlcv?symbol=RELIANCE&period=3mo` | Price history |
| `GET`  | `/market/headlines?category=markets` | ET headlines |
| `GET`  | `/health` | Health check |

---

## 🤖 Agent Capabilities

### Market Data Agent
- Live price, % change, 52-week high/low, volume, market cap
- OHLCV history (1 month to 5 years)
- Fundamentals: P/E, P/B, EPS, dividend yield, ROE, sector

### News & Filings Agent
- ET RSS feeds: markets, stocks, economy, mutual funds
- BSE corporate filings (earnings, board meetings, insider trades)
- Keyword-based relevance filtering across all feeds

### Technical Analysis Agent
- RSI-14 (oversold/overbought signals)
- MACD with signal line crossover detection
- Bollinger Bands (upper/lower breach alerts)
- SMA-20, SMA-50, SMA-200 (golden/death cross)
- Support & resistance via pivot points + swing high/low

### Portfolio Agent
- Parses CAMS and KFintech CSV statements
- Computes portfolio weights, P&L per fund
- Injects context into every Claude system prompt
- Flags overlap when user already holds queried stock/fund

---

## 💬 Example Queries

- *"Should I buy Reliance at current levels?"*
  → Live price + RSI + MACD + recent news + your portfolio weight in energy
  
- *"Why is HDFC Bank falling today?"*
  → ET news + BSE filings + technical breakdown

- *"Compare TCS vs Infosys fundamentals"*
  → Side-by-side P/E, P/B, ROE, revenue growth table

- *"What are today's top movers on NSE?"*
  → ET headlines + quote fetches for mentioned stocks

- *"Analyse my portfolio for sector risk"*
  → Uses your uploaded CAMS data to flag concentration

---

## 📂 Project Structure

```
marketmind/
├── backend/
│   ├── main.py              # FastAPI app + SSE routes
│   ├── config.py            # Environment config
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── orchestrator.py  # Claude tool-use + streaming
│   │   ├── market_data.py   # yfinance wrapper
│   │   ├── news.py          # ET RSS + BSE filings
│   │   ├── technical.py     # pandas-ta indicators
│   │   └── portfolio.py     # CAMS CSV parser
│   └── models/
│       └── schemas.py       # Pydantic models
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js    # SSE streaming client
│   │   ├── hooks/useChat.js # All chat state
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── ChatMessage.jsx
│   │       ├── ChatInput.jsx
│   │       ├── StockChart.jsx
│   │       ├── ThinkingSteps.jsx
│   │       ├── PortfolioPanel.jsx
│   │       └── WelcomeScreen.jsx
│   ├── package.json
│   └── vite.config.js
│
├── ARCHITECTURE.md
└── README.md
```

---

## 🎬 Demo Highlights

1. Ask any NSE/BSE question → watch the Reasoning panel show live agent calls
2. Upload a CAMS CSV → every answer becomes portfolio-aware
3. Ask about a specific stock → inline candlestick chart renders automatically
4. Multi-stock comparison → Claude fetches all data in parallel

---

## ⚠️ Disclaimer

This tool is for informational purposes only. It is not SEBI-registered investment advice. Always consult a qualified financial advisor before making investment decisions.

---

## 👥 Team

Built for the ET AI Hackathon 2026 (Phase 2: Build Sprint).
