import yfinance as yf
import pandas as pd
try:
    import pandas_ta as ta
    HAS_TA = True
except ImportError:
    HAS_TA = False
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _to_nse(symbol: str) -> str:
    s = symbol.upper().strip()
    if not s.endswith(".NS") and not s.endswith(".BO"):
        return s + ".NS"
    return s


def get_technical_analysis(symbol: str, period: str = "6mo") -> dict:
    """
    Compute RSI, MACD, Bollinger Bands, SMA-20/50/200,
    and a plain-English signal summary for the given symbol.
    """
    ticker_sym = _to_nse(symbol)
    try:
        df = yf.download(ticker_sym, period=period, auto_adjust=True, progress=False)
        if df.empty or len(df) < 30:
            return {"symbol": symbol, "error": "Insufficient data for TA"}

        df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower()
                      for c in df.columns]

        indicators = {}

        if HAS_TA:
            # RSI (14)
            rsi_series = ta.rsi(df["close"], length=14)
            if rsi_series is not None and not rsi_series.empty:
                indicators["rsi_14"] = round(rsi_series.iloc[-1], 2)

            # MACD (12, 26, 9)
            macd_df = ta.macd(df["close"])
            if macd_df is not None and not macd_df.empty:
                indicators["macd"]        = round(macd_df.iloc[-1, 0], 4)
                indicators["macd_signal"] = round(macd_df.iloc[-1, 2], 4)
                indicators["macd_hist"]   = round(macd_df.iloc[-1, 1], 4)

            # Bollinger Bands (20, 2)
            bb_df = ta.bbands(df["close"], length=20, std=2)
            if bb_df is not None and not bb_df.empty:
                indicators["bb_upper"] = round(bb_df.iloc[-1]["BBU_20_2.0"], 2)
                indicators["bb_mid"]   = round(bb_df.iloc[-1]["BBM_20_2.0"], 2)
                indicators["bb_lower"] = round(bb_df.iloc[-1]["BBL_20_2.0"], 2)

            # SMAs
            for length in [20, 50, 200]:
                sma = ta.sma(df["close"], length=length)
                if sma is not None and not sma.empty and pd.notna(sma.iloc[-1]):
                    indicators[f"sma_{length}"] = round(sma.iloc[-1], 2)

            # Volume SMA 20
            vsma = ta.sma(df["volume"], length=20)
            if vsma is not None and not vsma.empty and pd.notna(vsma.iloc[-1]):
                indicators["volume_sma_20"] = int(vsma.iloc[-1])

        else:
            # Fallback: manual computation without pandas_ta
            close = df["close"]
            indicators["sma_20"]  = round(close.rolling(20).mean().iloc[-1], 2)
            indicators["sma_50"]  = round(close.rolling(50).mean().iloc[-1], 2)

            delta  = close.diff()
            gain   = delta.clip(lower=0).rolling(14).mean()
            loss   = (-delta.clip(upper=0)).rolling(14).mean()
            rs     = gain / loss
            rsi    = 100 - (100 / (1 + rs))
            indicators["rsi_14"] = round(rsi.iloc[-1], 2)

        current_price = round(df["close"].iloc[-1], 2)
        indicators["current_price"] = current_price

        # Build human-readable signal
        signals  = []
        rsi_val  = indicators.get("rsi_14")
        if rsi_val:
            if rsi_val < 30:
                signals.append(f"RSI {rsi_val} → Oversold (potential buy signal)")
            elif rsi_val > 70:
                signals.append(f"RSI {rsi_val} → Overbought (potential sell signal)")
            else:
                signals.append(f"RSI {rsi_val} → Neutral")

        macd_val  = indicators.get("macd")
        macd_sig  = indicators.get("macd_signal")
        if macd_val is not None and macd_sig is not None:
            if macd_val > macd_sig:
                signals.append("MACD above signal line → Bullish momentum")
            else:
                signals.append("MACD below signal line → Bearish momentum")

        sma_50  = indicators.get("sma_50")
        sma_200 = indicators.get("sma_200")
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                signals.append("Golden cross (50 SMA > 200 SMA) → Long-term bullish")
            else:
                signals.append("Death cross (50 SMA < 200 SMA) → Long-term bearish")

        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        if bb_upper and bb_lower:
            if current_price >= bb_upper:
                signals.append("Price at upper Bollinger Band → Potential resistance")
            elif current_price <= bb_lower:
                signals.append("Price at lower Bollinger Band → Potential support")
            else:
                signals.append("Price within Bollinger Bands → Normal range")

        return {
            "symbol":     symbol.upper(),
            "period":     period,
            "indicators": indicators,
            "signals":    signals,
            "summary":    " | ".join(signals) if signals else "Insufficient data for signals",
            "source":     "NSE via Yahoo Finance + pandas-ta",
        }

    except Exception as e:
        logger.error(f"TA failed for {symbol}: {e}", exc_info=True)
        return {"symbol": symbol, "error": str(e)}


def get_support_resistance(symbol: str, period: str = "6mo") -> dict:
    """
    Identify key support and resistance levels using pivot points
    and recent swing highs/lows.
    """
    ticker_sym = _to_nse(symbol)
    try:
        df = yf.download(ticker_sym, period=period, auto_adjust=True, progress=False)
        if df.empty or len(df) < 20:
            return {"symbol": symbol, "error": "Insufficient data"}

        df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower()
                      for c in df.columns]

        # Classic pivot points (last complete week)
        last = df.iloc[-2]
        pivot  = round((last["high"] + last["low"] + last["close"]) / 3, 2)
        r1     = round((2 * pivot) - last["low"],  2)
        r2     = round(pivot + (last["high"] - last["low"]), 2)
        s1     = round((2 * pivot) - last["high"], 2)
        s2     = round(pivot - (last["high"] - last["low"]), 2)

        # Recent swing high/low (20-day window)
        recent        = df.tail(20)
        swing_high    = round(recent["high"].max(), 2)
        swing_low     = round(recent["low"].min(),  2)
        current_price = round(df["close"].iloc[-1], 2)

        return {
            "symbol":        symbol.upper(),
            "current_price": current_price,
            "pivot":         pivot,
            "resistance":    {"r1": r1, "r2": r2, "swing_high": swing_high},
            "support":       {"s1": s1, "s2": s2, "swing_low":  swing_low},
            "source":        "NSE via Yahoo Finance (calculated)",
        }
    except Exception as e:
        logger.error(f"S/R failed for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}
