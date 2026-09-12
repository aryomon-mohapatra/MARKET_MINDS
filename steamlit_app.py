"""
MarketMind — Streamlit App
Single-file deployment for Streamlit Cloud
Run locally: streamlit run streamlit_app.py
"""

import streamlit as st
import sys
import os
import json
import asyncio
import pandas as pd
import plotly.graph_objects as go
from io import StringIO

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from agents import market_data, news, technical
from agents.portfolio import parse_cams_csv, build_portfolio_context
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS
from groq import Groq

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketMind",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0D1B2A; }
    .stApp { background-color: #0D1B2A; }

    /* Header */
    .mm-header {
        background: linear-gradient(90deg, #0D1B2A 0%, #1B2A3B 100%);
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #00C9A733;
        margin-bottom: 1rem;
    }
    .mm-title { color: #FFFFFF; font-size: 1.6rem; font-weight: 800; margin: 0; }
    .mm-subtitle { color: #00C9A7; font-size: 0.75rem; letter-spacing: 0.1em; margin: 0; }

    /* Agent thinking steps */
    .thinking-box {
        background: #1B2A3B;
        border: 1px solid #00C9A733;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.82rem;
        color: #C5D8E0;
    }
    .agent-call {
        background: #243447;
        border-left: 3px solid #00C9A7;
        border-radius: 0 8px 8px 0;
        padding: 0.4rem 0.75rem;
        margin: 0.3rem 0;
        font-size: 0.8rem;
        color: #C5D8E0;
    }
    .agent-done {
        border-left-color: #10b981;
    }

    /* Portfolio card */
    .portfolio-card {
        background: #1B2A3B;
        border: 1px solid #00C9A733;
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .portfolio-stat { color: #00C9A7; font-size: 1.2rem; font-weight: 700; }
    .portfolio-label { color: #8BA3B0; font-size: 0.72rem; }

    /* Suggestion chips */
    .stButton button {
        background: #1B2A3B !important;
        border: 1px solid #243447 !important;
        color: #C5D8E0 !important;
        border-radius: 20px !important;
        font-size: 0.78rem !important;
        padding: 0.25rem 0.75rem !important;
        width: 100% !important;
        text-align: left !important;
    }
    .stButton button:hover {
        border-color: #00C9A7 !important;
        color: #00C9A7 !important;
    }

    /* Chat messages */
    .user-msg {
        background: #1B2A3B;
        border-radius: 12px 12px 4px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        color: #E8F4F1;
        font-size: 0.9rem;
    }
    .assistant-msg {
        background: #243447;
        border-radius: 4px 12px 12px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        color: #E8F4F1;
        font-size: 0.9rem;
        border-left: 3px solid #00C9A7;
    }
    .disclaimer {
        color: #8BA3B0;
        font-size: 0.72rem;
        font-style: italic;
        margin-top: 0.5rem;
    }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = None
if "portfolio_context" not in st.session_state:
    st.session_state.portfolio_context = None


# ── Groq client ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


# ── Tool definitions ───────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": "Fetch live stock price, % change, 52-week high/low, volume for NSE/BSE stocks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"},
                                "description": "NSE symbols e.g. ['RELIANCE', 'TCS']"}
                },
                "required": ["symbols"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Fetch OHLCV price history for charting and trend analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "period": {"type": "string", "enum": ["1mo", "3mo", "6mo", "1y", "2y"]},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_news",
            "description": "Fetch latest ET news and BSE filings for a company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "query":  {"type": "string"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_indicators",
            "description": "Compute RSI, MACD, Bollinger Bands, SMA, support/resistance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "period": {"type": "string", "enum": ["3mo", "6mo", "1y"]},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fundamentals",
            "description": "Fetch P/E, P/B, EPS, dividend yield, ROE for a stock.",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_headlines",
            "description": "Fetch top ET market headlines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string",
                                 "enum": ["markets", "stocks", "economy", "mutual_funds"]},
                },
            },
        },
    },
]


def execute_tool(name, tool_input):
    try:
        if name == "get_stock_quote":
            return market_data.get_quote(tool_input["symbols"])
        elif name == "get_price_history":
            return market_data.get_ohlcv(tool_input["symbol"], tool_input.get("period", "3mo"))
        elif name == "get_company_news":
            return news.get_company_news(tool_input["symbol"])
        elif name == "get_technical_indicators":
            ta = technical.get_technical_analysis(tool_input["symbol"], tool_input.get("period", "6mo"))
            sr = technical.get_support_resistance(tool_input["symbol"])
            return {**ta, "support_resistance": sr}
        elif name == "get_fundamentals":
            return market_data.get_fundamentals(tool_input["symbol"])
        elif name == "get_market_headlines":
            return {"headlines": news.fetch_et_headlines(tool_input.get("category", "markets"))}
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


def build_system_prompt():
    base = """You are MarketMind — an advanced AI analyst for Indian equity markets.

RULES:
1. Always cite sources: [Source: ET Markets], [Source: NSE via Yahoo Finance], [Source: BSE India]
2. Be specific with numbers: "up 3.2% to ₹2,847" not "the stock is up"
3. For buy/sell questions: give balanced view with RSI, trend, fundamentals, and risk
4. Format with ## headers, bullet points, tables where useful
5. End every response with: *This is AI-generated analysis, not SEBI-registered investment advice.*"""

    if st.session_state.portfolio_context:
        base += f"\n\n{st.session_state.portfolio_context}"
    return base


def render_chart(symbol, candles):
    """Render a candlestick + volume chart using Plotly."""
    if not candles:
        return
    df = pd.DataFrame(candles)
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"], high=df["high"],
        low=df["low"],   close=df["close"],
        name=symbol,
        increasing_line_color="#00C9A7",
        decreasing_line_color="#FF6B6B",
    ))

    fig.update_layout(
        title=f"{symbol} — Price Chart",
        paper_bgcolor="#1B2A3B",
        plot_bgcolor="#1B2A3B",
        font_color="#C5D8E0",
        xaxis_rangeslider_visible=False,
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="#243447"),
        yaxis=dict(gridcolor="#243447"),
    )
    st.plotly_chart(fig, use_container_width=True)


def run_query(query):
    """Run the full multi-agent pipeline and stream response."""
    client = get_groq_client()
    system  = build_system_prompt()

    history = []
    for m in st.session_state.messages[-10:]:
        history.append({"role": m["role"], "content": m["content"]})
    history.append({"role": "user", "content": query})

    messages = [{"role": "system", "content": system}] + history

    # ── Phase 1: Tool selection ────────────────────────────────────────────────
    thinking_placeholder = st.empty()
    steps = []

    def update_thinking():
        with thinking_placeholder.container():
            with st.expander("🧠 Reasoning", expanded=True):
                for step in steps:
                    if step["type"] == "thinking":
                        st.markdown(f"◆ *{step['content']}*")
                    elif step["type"] == "agent":
                        icon  = "✓" if step.get("done") else "⟳"
                        color = "#10b981" if step.get("done") else "#00C9A7"
                        st.markdown(
                            f'<div class="agent-call {"agent-done" if step.get("done") else ""}">'
                            f'{icon} <b>{step["label"]}</b>'
                            f'{" → " + step.get("result","") if step.get("done") else " — fetching…"}'
                            f'</div>', unsafe_allow_html=True
                        )

    steps.append({"type": "thinking", "content": "Analysing your query…"})
    update_thinking()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_msg  = response.choices[0].message
    tool_calls     = assistant_msg.tool_calls or []
    tool_results   = []
    chart_data     = []

    AGENT_LABELS = {
        "get_stock_quote":          "Live prices",
        "get_price_history":        "Price history",
        "get_company_news":         "ET News + BSE filings",
        "get_technical_indicators": "Technical analysis",
        "get_fundamentals":         "Fundamentals",
        "get_market_headlines":     "ET Headlines",
    }

    # ── Phase 2: Execute tools ────────────────────────────────────────────────
    for tc in tool_calls:
        name  = tc.function.name
        try:
            inp = json.loads(tc.function.arguments)
        except Exception:
            inp = {}

        label = AGENT_LABELS.get(name, name)
        sym   = inp.get("symbols", [inp.get("symbol", inp.get("category", ""))])
        sym_str = ", ".join(sym) if isinstance(sym, list) else str(sym)

        steps.append({"type": "agent", "label": f"{label} → {sym_str}", "done": False})
        update_thinking()

        result = execute_tool(name, inp)

        # Summary
        summary = ""
        if name == "get_stock_quote":
            parts = [f"{s} ₹{d.get('price','?')} ({d.get('change_pct',0):+.1f}%)"
                     for s, d in result.items() if isinstance(d, dict) and d.get("price")]
            summary = ", ".join(parts)
        elif name == "get_price_history":
            n = len(result.get("candles", []))
            summary = f"{n} trading days loaded"
            if result.get("candles"):
                chart_data.append({"symbol": result.get("symbol",""), "candles": result["candles"]})
        elif name == "get_company_news":
            summary = f"{len(result.get('et_news',[]))} articles + {len(result.get('bse_filings',[]))} filings"
        elif name == "get_technical_indicators":
            summary = result.get("summary", "")[:60]
        elif name == "get_fundamentals":
            summary = f"P/E={result.get('pe_ratio','N/A')}, sector={result.get('sector','N/A')}"
        elif name == "get_market_headlines":
            summary = f"{len(result.get('headlines',[]))} headlines"

        steps[-1]["done"]   = True
        steps[-1]["result"] = summary
        update_thinking()

        tool_results.append({
            "role":         "tool",
            "tool_call_id": tc.id,
            "content":      json.dumps(result, default=str),
        })

    # ── Phase 3: Streamed synthesis ───────────────────────────────────────────
    steps.append({"type": "thinking", "content": "Synthesizing insights…"})
    update_thinking()

    answer_placeholder = st.empty()
    full_answer = ""

    if not tool_calls:
        full_answer = assistant_msg.content or ""
        answer_placeholder.markdown(
            f'<div class="assistant-msg">{full_answer}</div>', unsafe_allow_html=True
        )
    else:
        synthesis_messages = messages + [
            {
                "role":       "assistant",
                "content":    assistant_msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in tool_calls
                ],
            },
            *tool_results,
        ]

        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=MAX_TOKENS,
            messages=synthesis_messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_answer += delta
                answer_placeholder.markdown(
                    f'<div class="assistant-msg">{full_answer}▋</div>',
                    unsafe_allow_html=True
                )

        answer_placeholder.markdown(
            f'<div class="assistant-msg">{full_answer}</div>', unsafe_allow_html=True
        )

    thinking_placeholder.empty()

    # Render charts
    for cd in chart_data:
        render_chart(cd["symbol"], cd["candles"])

    return full_answer


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-header">
  <p class="mm-title">📈 MarketMind</p>
  <p class="mm-subtitle">MULTI-AGENT MARKET INTELLIGENCE · ET AI HACKATHON 2026</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Portfolio")

    uploaded = st.file_uploader("Upload CAMS / KFintech CSV", type=["csv"])
    if uploaded:
        try:
            content = uploaded.read()
            result  = parse_cams_csv(content)
            if "error" not in result:
                st.session_state.portfolio         = result
                st.session_state.portfolio_context = build_portfolio_context(result)
                st.success("Portfolio loaded!")
            else:
                st.error(result["error"])
        except Exception as e:
            st.error(str(e))

    if st.session_state.portfolio:
        p = st.session_state.portfolio
        total_v = p.get("total_value", 0)
        total_i = p.get("total_invested", 0)
        gain    = total_v - total_i
        gain_pct = p.get("gain_pct", 0)

        col1, col2 = st.columns(2)
        col1.metric("Current Value",  f"₹{total_v/100000:.1f}L")
        col2.metric("Overall P&L",    f"{gain_pct:+.1f}%")

        st.markdown("**Holdings**")
        for h in p.get("holdings", [])[:8]:
            name = h.get("fund_name","")[:35]
            cv   = h.get("current_value", 0) or 0
            iv   = h.get("invested_value", 0) or 0
            g    = cv - iv
            gpct = (g / iv * 100) if iv else 0
            color = "🟢" if gpct >= 0 else "🔴"
            st.markdown(f"{color} **{name[:28]}**  \n₹{cv:,.0f} · {gpct:+.1f}%")

    st.markdown("---")
    st.markdown("### 💡 Try asking")
    suggestions = [
        "What is Reliance's current price?",
        "Technical analysis of TCS",
        "Why is Adani Enterprises moving?",
        "Compare HDFC Bank vs ICICI Bank",
        "Top market movers today",
        "Analyse my portfolio risk",
    ]
    for s in suggestions:
        if st.button(s, key=f"sug_{s}"):
            st.session_state["pending_query"] = s

    st.markdown("---")
    if st.button("🗑 Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style='font-size:0.7rem; color:#8BA3B0; margin-top:1rem;'>
    Not SEBI-registered advice.<br>
    Built with Groq · LLaMA 3.3 70B<br>
    FastAPI · yfinance · pandas-ta
    </div>
    """, unsafe_allow_html=True)


# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    css_class = "user-msg" if msg["role"] == "user" else "assistant-msg"
    st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)


# ── Chat input ────────────────────────────────────────────────────────────────
query = st.chat_input("Ask anything about Indian markets…")

# Handle suggestion button clicks
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    # Show user message
    st.markdown(f'<div class="user-msg">{query}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": query})

    # Run pipeline
    with st.spinner(""):
        answer = run_query(query)

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
