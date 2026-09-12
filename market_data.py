import yfinance as yf
import pandas as pd
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _to_nse(symbol: str) -> str:
    """Convert bare symbol to NSE Yahoo Finance format."""
    s = symbol.upper().strip()
    if not s.endswith(".NS") and not s.endswith(".BO"):
        return s + ".NS"
    return s


def get_quote(symbols: List[str]) -> dict:
    """
    Fetch live quote for one or more NSE symbols.
    Returns price, change%, volume, 52w high/low.
    """
    results = {}
    for sym in symbols:
        ticker_sym = _to_nse(sym)
        try:
            t = yf.Ticker(ticker_sym)
            info = t.fast_info

            price    = getattr(info, "last_price", None)
            prev     = getattr(info, "previous_close", None)
            high_52  = getattr(info, "year_high", None)
            low_52   = getattr(info, "year_low", None)
            volume   = getattr(info, "last_volume", None)
            mktcap   = getattr(info, "market_cap", None)

            change_pct = None
            if price and prev and prev != 0:
                change_pct = round(((price - prev) / prev) * 100, 2)

            results[sym.upper()] = {
                "symbol":       sym.upper(),
                "ticker":       ticker_sym,
                "price":        round(price, 2)   if price   else None,
                "prev_close":   round(prev, 2)    if prev    else None,
                "change_pct":   change_pct,
                "high_52w":     round(high_52, 2) if high_52 else None,
                "low_52w":      round(low_52, 2)  if low_52  else None,
                "volume":       int(volume)        if volume  else None,
                "market_cap":   mktcap,
                "as_of":        datetime.utcnow().isoformat() + "Z",
                "source":       "NSE via Yahoo Finance",
                "source_url":   f"https://finance.yahoo.com/quote/{ticker_sym}",
            }
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {sym}: {e}")
            results[sym.upper()] = {"symbol": sym.upper(), "error": str(e)}

    return results


def get_ohlcv(symbol: str, period: str = "3mo") -> dict:
    """
    Fetch OHLCV history for charting.
    period: 1d | 5d | 1mo | 3mo | 6mo | 1y | 2y | 5y
    """
    ticker_sym = _to_nse(symbol)
    try:
        t  = yf.Ticker(ticker_sym)
        df = t.history(period=period, auto_adjust=True)

        if df.empty:
            return {"symbol": symbol, "error": "No data returned", "candles": []}

        candles = []
        for ts, row in df.iterrows():
            candles.append({
                "date":   ts.strftime("%Y-%m-%d"),
                "open":   round(row["Open"],   2),
                "high":   round(row["High"],   2),
                "low":    round(row["Low"],    2),
                "close":  round(row["Close"],  2),
                "volume": int(row["Volume"])  if pd.notna(row["Volume"]) else 0,
            })

        return {
            "symbol":  symbol.upper(),
            "period":  period,
            "candles": candles,
            "source":  "NSE via Yahoo Finance",
        }
    except Exception as e:
        logger.error(f"OHLCV fetch failed for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e), "candles": []}


def get_fundamentals(symbol: str) -> dict:
    """Fetch P/E, P/B, EPS, dividend yield from yfinance info dict."""
    ticker_sym = _to_nse(symbol)
    try:
        t    = yf.Ticker(ticker_sym)
        info = t.info
        return {
            "symbol":          symbol.upper(),
            "pe_ratio":        info.get("trailingPE"),
            "pb_ratio":        info.get("priceToBook"),
            "eps":             info.get("trailingEps"),
            "dividend_yield":  info.get("dividendYield"),
            "roe":             info.get("returnOnEquity"),
            "debt_to_equity":  info.get("debtToEquity"),
            "revenue_growth":  info.get("revenueGrowth"),
            "profit_margins":  info.get("profitMargins"),
            "sector":          info.get("sector"),
            "industry":        info.get("industry"),
            "source":          "Yahoo Finance",
            "source_url":      f"https://finance.yahoo.com/quote/{ticker_sym}",
        }
    except Exception as e:
        logger.error(f"Fundamentals fetch failed for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}
