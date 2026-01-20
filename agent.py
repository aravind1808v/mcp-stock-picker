import asyncio
from typing import TypedDict, Optional, Any, Dict

from langgraph.graph import StateGraph, END

# This is the MCP client side. Exact import depends on your MCP python client.
# Many setups use something like:
# from mcp.client import ClientSession
# from mcp.client.stdio import stdio_client
#
# I’ll write it as a thin wrapper so you can swap implementation.

class StockState(TypedDict, total=False):
    ticker: str
    price: Dict[str, Any]
    fin: Dict[str, Any]
    news: Dict[str, Any]
    sma_50: Dict[str, Any]
    short: Dict[str, Any]
    final: Dict[str, Any]


class MCPTools:
    """
    Minimal wrapper around your MCP connection.
    Replace internals with your actual MCP python client.
    """
    def __init__(self):
        self._session = None

    async def __aenter__(self):
        # connect to MCP server (stdio/http)
        # self._session = await ...
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # close session
        return

    async def call(self, tool: str, **kwargs) -> dict:
        # return await self._session.call_tool(tool, kwargs)
        raise NotImplementedError("Wire this to your MCP client implementation.")


async def fetch_all_tools(state: StockState) -> StockState:
    ticker = state["ticker"]

    async with MCPTools() as tools:
        # run in parallel
        price_task = tools.call("price_history", ticker=ticker, days=365)
        fin_task   = tools.call("financials", ticker=ticker, limit=4)
        news_task  = tools.call("news", ticker=ticker, limit=10)
        sma_task   = tools.call("sma", ticker=ticker, window=50, days=365)
        short_task = tools.call("short_interest", ticker=ticker)

        price, fin, nws, sma50, short = await asyncio.gather(
            price_task, fin_task, news_task, sma_task, short_task
        )

    state["price"] = price
    state["fin"] = fin
    state["news"] = nws
    state["sma_50"] = sma50
    state["short"] = short
    return state


def decide(state: StockState) -> StockState:
    """
    Deterministic decision policy (great for interviews).
    You can later replace with an LLM-based summarizer,
    but keep the rating logic explicit.
    """
    ticker = state["ticker"].upper()
    sma50 = state.get("sma_50", {})
    fin = state.get("fin", {})
    nws = state.get("news", {})

    # --- Technical signal example ---
    pct_vs_sma = sma50.get("pct_vs_sma")
    tech = "neutral"
    if isinstance(pct_vs_sma, (int, float)):
        if pct_vs_sma > 3:
            tech = "bullish"
        elif pct_vs_sma < -3:
            tech = "bearish"

    # --- Fundamental heuristic example (placeholder) ---
    # You can compute revenue growth, margins, FCF trend, etc.
    fundamentals = "unknown"
    if fin.get("results"):
        fundamentals = "ok"  # replace with real scoring

    # --- News heuristic example (placeholder) ---
    news_items = nws.get("results", [])
    news_signal = "neutral"
    if len(news_items) == 0:
        news_signal = "neutral"
    else:
        news_signal = "mixed"  # replace with sentiment scoring if desired

    # --- Simple scoring ---
    score = 0
    score += 1 if tech == "bullish" else -1 if tech == "bearish" else 0
    score += 1 if fundamentals in ("strong", "ok") else 0
    score += -1 if news_signal == "negative" else 0

    if score >= 2:
        rating = "BUY"
    elif score <= -1:
        rating = "SELL"
    else:
        rating = "HOLD"

    state["final"] = {
        "ticker": ticker,
        "rating": rating,
        "score": score,
        "drivers": {
            "technical": {"pct_vs_sma_50": pct_vs_sma, "signal": tech},
            "fundamentals": fundamentals,
            "news": {"count": len(news_items), "signal": news_signal},
        },
        "notes": [
            "This is a heuristic rating; refine with explicit fundamental metrics and better news scoring."
        ],
        "sources": [
            # pull URLs from Polygon news payload if present
            *(item.get("article_url") for item in news_items if item.get("article_url"))
        ][:10],
    }
    return state


def build_graph():
    g = StateGraph(StockState)
    g.add_node("fetch_all", fetch_all_tools)
    g.add_node("decide", decide)

    g.set_entry_point("fetch_all")
    g.add_edge("fetch_all", "decide")
    g.add_edge("decide", END)

    return g.compile()


# entrypoint
async def analyze_stock(ticker: str) -> dict:
    graph = build_graph()
    final_state = await graph.ainvoke({"ticker": ticker})
    return final_state["final"]


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(analyze_stock("AAPL")))
