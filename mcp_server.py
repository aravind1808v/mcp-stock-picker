import os
import httpx
from datetime import datetime, timedelta
from fastmcp import FastMCP

mcp = FastMCP("massive-polygon-tools")

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE = "https://api.polygon.io"

def _require_key():
    if not POLYGON_API_KEY:
        raise RuntimeError("Missing POLYGON_API_KEY in environment.")

@mcp.tool()
async def price_history(ticker: str, days: int = 365) -> dict:
    """
    Fetch daily OHLCV bars for the last N days.
    """
    _require_key()
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)

    url = f"{BASE}/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start}/{end}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": POLYGON_API_KEY}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def financials(ticker: str, limit: int = 4) -> dict:
    """
    Fetch recent financials (income statement / balance sheet / cash flow if available).
    """
    _require_key()
    url = f"{BASE}/vX/reference/financials"
    params = {"ticker": ticker.upper(), "limit": limit, "apiKey": POLYGON_API_KEY}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def news(ticker: str, limit: int = 10) -> dict:
    """
    Fetch recent news for the ticker.
    """
    _require_key()
    url = f"{BASE}/v2/reference/news"
    params = {"ticker": ticker.upper(), "limit": limit, "apiKey": POLYGON_API_KEY}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

@mcp.tool()
async def sma(ticker: str, window: int = 50, days: int = 365) -> dict:
    """
    Compute SMA from price history (simple local calc).
    """
    data = await price_history(ticker=ticker, days=days)
    results = data.get("results", [])
    closes = [bar["c"] for bar in results if "c" in bar]

    if len(closes) < window:
        return {"ticker": ticker.upper(), "window": window, "error": "Not enough data"}

    sma_values = []
    running = sum(closes[:window])
    sma_values.append(running / window)
    for i in range(window, len(closes)):
        running += closes[i] - closes[i - window]
        sma_values.append(running / window)

    # align with dates: SMA starts at index window-1
    sma_last = sma_values[-1]
    last_close = closes[-1]
    return {
        "ticker": ticker.upper(),
        "window": window,
        "last_close": last_close,
        "sma_last": sma_last,
        "pct_vs_sma": (last_close - sma_last) / sma_last * 100.0,
        "n_points": len(sma_values),
    }

@mcp.tool()
async def short_interest(ticker: str) -> dict:
    """
    Short interest is often source-dependent. If Polygon endpoint isn't available in your plan,
    keep this as a placeholder or integrate another provider.
    """
    # Placeholder – implement with the exact endpoint you have access to.
    return {"ticker": ticker.upper(), "note": "Implement with provider endpoint you have access to."}

if __name__ == "__main__":
    # FastMCP CLI patterns vary by version; common approach:
    # python mcp_server.py
    mcp.run()

