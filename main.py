"""
MarketMind — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from config import PORT
from agents.orchestrator import stream_response
from agents.portfolio import parse_cams_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MarketMind backend starting up…")
    yield
    logger.info("MarketMind backend shutting down…")


app = FastAPI(
    title="MarketMind",
    description="AI-powered Indian markets analyst — ET AI Hackathon 2026",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────────────────

class MessageIn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    conversation_history: List[MessageIn] = []
    portfolio_context: Optional[Dict[str, Any]] = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "marketmind"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    Each event is a JSON object prefixed with 'data: '.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    history = [{"role": m.role, "content": m.content}
               for m in request.conversation_history]

    async def event_generator():
        try:
            async for chunk in stream_response(
                query=request.query,
                conversation_history=history,
                portfolio_data=request.portfolio_context,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":   "no-cache",
            "X-Accel-Buffering":"no",
        },
    )


@app.post("/portfolio/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    Accept a CAMS or KFintech CSV and return a parsed portfolio summary.
    The frontend stores this in state and sends it with every chat request.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        content = await file.read()
        result  = parse_cams_csv(content)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/quote")
async def market_quote(symbols: str):
    """Quick quote endpoint (comma-separated symbols). e.g. ?symbols=RELIANCE,TCS"""
    from agents.market_data import get_quote
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="Provide at least one symbol")
    return get_quote(sym_list)


@app.get("/market/ohlcv")
async def market_ohlcv(symbol: str, period: str = "3mo"):
    """OHLCV history for chart rendering."""
    from agents.market_data import get_ohlcv
    return get_ohlcv(symbol, period)


@app.get("/market/headlines")
async def market_headlines(category: str = "markets", limit: int = 10):
    """Latest ET headlines."""
    from agents.news import fetch_et_headlines
    return {"headlines": fetch_et_headlines(category, limit)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
