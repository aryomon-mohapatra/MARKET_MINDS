import pandas as pd
import io
import re
import logging
from typing import Optional
from datetime import date, datetime

logger = logging.getLogger(__name__)


# ── CAMS / KFintech CSV parsing ────────────────────────────────────────────────

def parse_cams_csv(file_bytes: bytes) -> dict:
    """
    Parse a CAMS mutual fund statement CSV.
    Returns standardised portfolio summary.
    """
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
        df   = pd.read_csv(io.StringIO(text), skiprows=_detect_header_row(text))
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Normalise column names across CAMS variants
        col_map = {
            "scheme_name":        ["scheme_name", "fund_name", "scheme"],
            "units":              ["units", "balance_units", "unit_balance"],
            "nav":                ["nav", "nav_per_unit"],
            "current_value":      ["current_value", "market_value", "current_mkt_value"],
            "invested_value":     ["invested_value", "cost_value", "total_cost"],
            "folio_no":           ["folio_no", "folio", "folio_number"],
        }
        df = _normalise_columns(df, col_map)

        holdings = []
        for _, row in df.iterrows():
            scheme = str(row.get("scheme_name", "")).strip()
            if not scheme or scheme.lower() in ("nan", "total", ""):
                continue
            holdings.append({
                "fund_name":      scheme,
                "folio":          str(row.get("folio_no", "")),
                "units":          _safe_float(row.get("units")),
                "nav":            _safe_float(row.get("nav")),
                "current_value":  _safe_float(row.get("current_value")),
                "invested_value": _safe_float(row.get("invested_value")),
            })

        total_invested = sum(h["invested_value"] or 0 for h in holdings)
        total_value    = sum(h["current_value"]  or 0 for h in holdings)
        overall_gain   = total_value - total_invested
        gain_pct       = (overall_gain / total_invested * 100) if total_invested else 0

        return {
            "source":           "CAMS Statement",
            "total_invested":   round(total_invested, 2),
            "total_value":      round(total_value, 2),
            "overall_gain":     round(overall_gain, 2),
            "gain_pct":         round(gain_pct, 2),
            "holdings":         holdings,
            "holding_count":    len(holdings),
        }
    except Exception as e:
        logger.error(f"CAMS parse error: {e}", exc_info=True)
        return {"error": str(e)}


def _detect_header_row(text: str) -> int:
    """Try to find which row the CSV header starts."""
    for i, line in enumerate(text.split("\n")[:20]):
        if re.search(r"scheme|fund|folio", line, re.IGNORECASE):
            return i
    return 0


def _normalise_columns(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    rename = {}
    for canonical, variants in col_map.items():
        for col in df.columns:
            if col in variants and canonical not in df.columns:
                rename[col] = canonical
    return df.rename(columns=rename)


def _safe_float(val) -> Optional[float]:
    try:
        cleaned = re.sub(r"[₹,\s]", "", str(val))
        return float(cleaned)
    except Exception:
        return None


# ── Portfolio context builder ──────────────────────────────────────────────────

def build_portfolio_context(portfolio_data: dict) -> str:
    """
    Convert portfolio dict → plain-English context string
    injected into the LLM system prompt.
    """
    if not portfolio_data:
        return ""

    lines = ["USER PORTFOLIO CONTEXT (inject in every answer):"]

    total_v   = portfolio_data.get("total_value",    0)
    total_i   = portfolio_data.get("total_invested", 0)
    gain_pct  = portfolio_data.get("gain_pct",       0)

    if total_v:
        lines.append(
            f"Portfolio value: ₹{total_v:,.0f} | Invested: ₹{total_i:,.0f} | "
            f"Overall gain: {gain_pct:+.1f}%"
        )

    holdings = portfolio_data.get("holdings", [])
    if holdings:
        lines.append(f"\nHoldings ({len(holdings)} funds):")
        for h in holdings[:10]:                     # top 10 only to save tokens
            name   = h.get("fund_name", "")[:60]
            cv     = h.get("current_value", 0) or 0
            iv     = h.get("invested_value", 0) or 0
            gain   = cv - iv
            wt     = (cv / total_v * 100) if total_v else 0
            lines.append(f"  • {name} — ₹{cv:,.0f} ({wt:.1f}% of portfolio, {gain:+,.0f} gain)")

    sector_breakdown = portfolio_data.get("sector_breakdown", {})
    if sector_breakdown:
        lines.append("\nSector allocation:")
        for sector, pct in sorted(sector_breakdown.items(), key=lambda x: -x[1])[:6]:
            lines.append(f"  • {sector}: {pct:.1f}%")

    return "\n".join(lines)


def analyse_portfolio_overlap(portfolio_data: dict, query_symbols: list) -> dict:
    """
    Check if user already holds any of the queried stocks/funds.
    Returns overlap warnings to include in response.
    """
    if not portfolio_data or not query_symbols:
        return {}

    holdings   = portfolio_data.get("holdings", [])
    fund_names = " ".join(h.get("fund_name", "").lower() for h in holdings)

    overlaps = {}
    for sym in query_symbols:
        sym_lower = sym.lower()
        if sym_lower in fund_names or sym_lower.replace("_", " ") in fund_names:
            overlaps[sym] = "Already present in your portfolio"

    return overlaps
