from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    role: str          # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    conversation_history: List[Message] = []
    portfolio_context: Optional[Dict[str, Any]] = None


class PortfolioHolding(BaseModel):
    symbol: str
    name: str
    quantity: float
    avg_cost: float
    current_value: Optional[float] = None
    weight_pct: Optional[float] = None


class PortfolioSummary(BaseModel):
    total_invested: float
    current_value: float
    holdings: List[PortfolioHolding]
    sector_breakdown: Dict[str, float]
    xirr: Optional[float] = None
