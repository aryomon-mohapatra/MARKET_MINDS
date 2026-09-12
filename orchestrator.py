"""
Orchestrator Agent — Groq Edition
──────────────────────────────────
Uses Groq's OpenAI-compatible API with llama-3.3-70b-versatile:
  1. First call with tools → model decides which agents to invoke
  2. Execute all tool calls in parallel (asyncio)
  3. Second call with tool results → streamed final answer
  4. Yield SSE-ready dicts throughout for the frontend
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, List, Optional
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS
from agents import market_data, news, technical, portfolio as portfolio_agent

logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)


# ── Tool Definitions (OpenAI function-calling format) ──────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": (
                "Fetch live stock price, % change, 52-week high/low, volume, and market cap "
                "for one or more NSE/BSE listed companies. Call this for any question about "
                "current price or recent price movement."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "NSE symbols, e.g. ['RELIANCE', 'HDFCBANK', 'TCS']",
                    }
                },
                "required": ["symbols"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": (
                "Fetch OHLCV (candlestick) price history for a single stock. "
                "Use when the user asks about trends, charts, or historical returns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE symbol, e.g. 'RELIANCE'"},
                    "period": {
                        "type": "string",
                        "enum": ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                        "description": "How far back to fetch data",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_news_and_filings",
            "description": (
                "Fetch latest ET news articles and BSE corporate filings for a company. "
                "Call this when the user asks about recent news, events, announcements, "
                "or why a stock is moving."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE symbol"},
                    "query":  {"type": "string", "description": "Search keywords for news"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_indicators",
            "description": (
                "Compute RSI, MACD, Bollinger Bands, SMA-20/50/200, and support/resistance "
                "levels for a stock. Use for technical analysis or buy/sell questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE symbol"},
                    "period": {
                        "type": "string",
                        "enum": ["3mo", "6mo", "1y"],
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_fundamentals",
            "description": (
                "Fetch P/E ratio, P/B ratio, EPS, dividend yield, ROE, and sector. "
                "Use for valuation questions or long-term investment analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "NSE symbol"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_headlines",
            "description": (
                "Fetch top market headlines from Economic Times. "
                "Use for broad market questions or 'what's happening in the market today'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["markets", "stocks", "economy", "mutual_funds"],
                    },
                    "limit": {"type": "integer"},
                },
            },
        },
    },
]


# ── Tool Executor ──────────────────────────────────────────────────────────────

def execute_tool(name: str, tool_input: dict) -> dict:
    try:
        if name == "get_stock_quote":
            return market_data.get_quote(tool_input["symbols"])

        elif name == "get_price_history":
            return market_data.get_ohlcv(
                tool_input["symbol"],
                tool_input.get("period", "3mo"),
            )

        elif name == "get_company_news_and_filings":
            result = news.get_company_news(tool_input["symbol"])
            if tool_input.get("query"):
                result["query_news"] = news.search_et_news(tool_input["query"])
            return result

        elif name == "get_technical_indicators":
            ta = technical.get_technical_analysis(
                tool_input["symbol"], tool_input.get("period", "6mo")
            )
            sr = technical.get_support_resistance(tool_input["symbol"])
            return {**ta, "support_resistance": sr}

        elif name == "get_stock_fundamentals":
            return market_data.get_fundamentals(tool_input["symbol"])

        elif name == "get_market_headlines":
            return {
                "headlines": news.fetch_et_headlines(
                    tool_input.get("category", "markets"),
                    tool_input.get("limit", 8),
                )
            }

        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return {"error": str(e)}


# ── System Prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(portfolio_context=None):
    base = """You are MarketMind — an advanced AI analyst for Indian equity markets built on live NSE/BSE data and Economic Times news.

Your goal: give retail Indian investors ACTIONABLE, data-backed, cited answers.

RULES:
1. Always cite sources inline: [Source: Economic Times], [Source: NSE via Yahoo Finance], etc.
2. Reference the user's portfolio when relevant — flag overexposure, existing holdings, concentration risk.
3. Be specific with numbers: "up 3.2% to ₹2,847 [Source: NSE]" not "the stock is up".
4. For buy/sell questions: give a balanced view with RSI, trend, fundamentals, and risk.
5. Format with ## headers, bullet points, and tables where useful.
6. End every response with: *This is AI-generated market analysis, not SEBI-registered investment advice.*"""

    if portfolio_context:
        base += f"\n\n{portfolio_context}"
    return base


# ── Main Streaming Orchestrator ────────────────────────────────────────────────

async def stream_response(
    query: str,
    conversation_history: List[dict],
    portfolio_data=None,
) -> AsyncGenerator[dict, None]:
    """
    Yields SSE-ready dicts:
      {"type": "thinking",     "content": "..."}
      {"type": "agent_call",   "agent": "...", "input": {...}}
      {"type": "agent_result", "agent": "...", "summary": "..."}
      {"type": "stream",       "content": "..."}
      {"type": "chart_data",   "symbol": "...", "candles": [...]}
      {"type": "done"}
      {"type": "error",        "message": "..."}
    """
    portfolio_context_str = (
        portfolio_agent.build_portfolio_context(portfolio_data) if portfolio_data else None
    )
    system = _build_system_prompt(portfolio_context_str)

    messages = [{"role": "system", "content": system}]
    for m in conversation_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": query})

    yield {"type": "thinking", "content": "Analysing your query…"}
    await asyncio.sleep(0)

    # Phase 1: Tool selection
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=MAX_TOKENS,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        )
    except Exception as e:
        yield {"type": "error", "message": f"Groq API error: {e}"}
        return

    assistant_message  = response.choices[0].message
    tool_calls         = assistant_message.tool_calls or []
    chart_data_to_emit = []
    tool_result_messages = []

    # Phase 2: Execute tool calls
    for tc in tool_calls:
        tool_name = tc.function.name
        try:
            tool_input = json.loads(tc.function.arguments)
        except json.JSONDecodeError:
            tool_input = {}

        yield {"type": "agent_call", "agent": tool_name, "input": tool_input}
        await asyncio.sleep(0)

        result  = await asyncio.get_event_loop().run_in_executor(
            None, execute_tool, tool_name, tool_input
        )
        summary = _summarise_tool_result(tool_name, result)

        yield {"type": "agent_result", "agent": tool_name, "summary": summary}
        await asyncio.sleep(0)

        if tool_name == "get_price_history" and result.get("candles"):
            chart_data_to_emit.append({
                "symbol":  result.get("symbol", tool_input.get("symbol", "")),
                "period":  result.get("period", ""),
                "candles": result["candles"],
            })

        tool_result_messages.append({
            "role":         "tool",
            "tool_call_id": tc.id,
            "content":      json.dumps(result, default=str),
        })

    # Phase 3: Streamed synthesis
    if not tool_calls:
        direct_text = assistant_message.content or ""
        for word in direct_text.split(" "):
            yield {"type": "stream", "content": word + " "}
            await asyncio.sleep(0.005)
    else:
        synthesis_messages = messages + [
            {
                "role":       "assistant",
                "content":    assistant_message.content or "",
                "tool_calls": [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            },
            *tool_result_messages,
        ]

        yield {"type": "thinking", "content": "Synthesizing insights…"}
        await asyncio.sleep(0)

        try:
            stream = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=GROQ_MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=synthesis_messages,
                    stream=True,
                )
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield {"type": "stream", "content": delta}
                    await asyncio.sleep(0)

        except Exception as e:
            yield {"type": "error", "message": f"Synthesis error: {e}"}
            return

    for cd in chart_data_to_emit:
        yield {"type": "chart_data", **cd}
        await asyncio.sleep(0)

    yield {"type": "done"}


# ── Helper ─────────────────────────────────────────────────────────────────────

def _summarise_tool_result(tool_name: str, result: dict) -> str:
    if "error" in result:
        return f"⚠ Error: {result['error']}"

    if tool_name == "get_stock_quote":
        parts = []
        for sym, data in result.items():
            if isinstance(data, dict) and data.get("price"):
                chg = data.get("change_pct")
                chg_str = f" ({chg:+.2f}%)" if chg is not None else ""
                parts.append(f"{sym} ₹{data['price']}{chg_str}")
        return "Live prices: " + ", ".join(parts) if parts else "Quotes fetched"

    if tool_name == "get_price_history":
        n = len(result.get("candles", []))
        return f"Loaded {n} trading days for {result.get('symbol', '')}"

    if tool_name == "get_company_news_and_filings":
        n_news = len(result.get("et_news", []))
        n_fil  = len(result.get("bse_filings", []))
        return f"{n_news} ET articles + {n_fil} BSE filings for {result.get('symbol', '')}"

    if tool_name == "get_technical_indicators":
        return f"TA: {result.get('summary','')[:80]}"

    if tool_name == "get_stock_fundamentals":
        return f"P/E={result.get('pe_ratio')}, sector={result.get('sector','N/A')}"

    if tool_name == "get_market_headlines":
        return f"Fetched {len(result.get('headlines', []))} ET headlines"

    return f"{tool_name} completed"
