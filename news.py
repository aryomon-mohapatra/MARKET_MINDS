import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import logging
import re

logger = logging.getLogger(__name__)

ET_FEEDS = {
    "markets":     "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "stocks":      "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "economy":     "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
    "mutual_funds":"https://economictimes.indiatimes.com/mf/rssfeeds/13357270.cms",
}

BSE_FILINGS_URL = (
    "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w?"
    "strCat=-1&strPrevDate={date}&strScrip={scrip}&strType=C&strName=&strAttchmt=N"
)


def _parse_entry(entry) -> dict:
    pub = entry.get("published", "") or entry.get("updated", "")
    return {
        "title":   entry.get("title", "").strip(),
        "summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()[:300],
        "link":    entry.get("link", ""),
        "published": pub,
        "source":  "Economic Times",
    }


def fetch_et_headlines(category: str = "markets", limit: int = 10) -> List[dict]:
    """Fetch latest ET headlines for a given category."""
    url = ET_FEEDS.get(category, ET_FEEDS["markets"])
    try:
        feed    = feedparser.parse(url)
        entries = feed.entries[:limit]
        return [_parse_entry(e) for e in entries]
    except Exception as e:
        logger.error(f"ET feed fetch failed ({category}): {e}")
        return []


def search_et_news(query: str, limit: int = 8) -> List[dict]:
    """
    Search ET news by querying all feeds and filtering by keywords.
    """
    keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
    results  = []

    for category, url in ET_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title   = entry.get("title", "").lower()
                summary = entry.get("summary", "").lower()
                text    = title + " " + summary
                if any(kw in text for kw in keywords):
                    parsed = _parse_entry(entry)
                    parsed["relevance_category"] = category
                    results.append(parsed)
        except Exception as e:
            logger.warning(f"Feed {category} error: {e}")

    # deduplicate by title
    seen   = set()
    unique = []
    for item in results:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    return unique[:limit]


def fetch_bse_filings(scrip_code: str, limit: int = 5) -> List[dict]:
    """
    Fetch recent corporate filings from BSE for a given scrip code.
    Common codes: RELIANCE=500325, HDFC BANK=500180, TCS=532540, INFY=500209
    """
    today = datetime.today().strftime("%Y%m%d")
    url   = BSE_FILINGS_URL.format(date=today, scrip=scrip_code)
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://www.bseindia.com",
        })
        if resp.status_code != 200:
            return []
        data     = resp.json()
        filings  = data.get("Table", [])[:limit]
        result   = []
        for f in filings:
            result.append({
                "title":      f.get("HEADLINE", ""),
                "category":   f.get("CATEGORYNAME", ""),
                "date":       f.get("DT_TM", ""),
                "scrip_code": scrip_code,
                "source":     "BSE India",
                "source_url": f"https://www.bseindia.com/stock-share-price/{scrip_code}",
            })
        return result
    except Exception as e:
        logger.error(f"BSE filings fetch failed for {scrip_code}: {e}")
        return []


# Map common NSE symbols → BSE scrip codes for filing lookups
NSE_TO_BSE = {
    "RELIANCE":   "500325",
    "HDFCBANK":   "500180",
    "TCS":        "532540",
    "INFY":       "500209",
    "WIPRO":      "507685",
    "ICICIBANK":  "532174",
    "HINDUNILVR": "500696",
    "ITC":        "500875",
    "SBIN":       "500112",
    "BAJFINANCE": "500034",
    "TATAMOTORS": "500570",
    "MARUTI":     "532500",
    "SUNPHARMA":  "524715",
    "DRREDDY":    "500124",
    "ADANIENT":   "512599",
    "LTIM":       "540005",
    "ONGC":       "500312",
    "POWERGRID":  "532898",
    "COALINDIA":  "533278",
    "NTPC":       "532555",
}


def get_company_news(nse_symbol: str, limit: int = 6) -> dict:
    """
    Combined: ET news + BSE filings for a given NSE symbol.
    """
    symbol_clean = nse_symbol.upper().replace(".NS", "").replace(".BO", "")

    et_news  = search_et_news(symbol_clean, limit=limit)
    filings  = []
    bse_code = NSE_TO_BSE.get(symbol_clean)
    if bse_code:
        filings = fetch_bse_filings(bse_code, limit=5)

    return {
        "symbol":      symbol_clean,
        "et_news":     et_news,
        "bse_filings": filings,
        "total_items": len(et_news) + len(filings),
    }
