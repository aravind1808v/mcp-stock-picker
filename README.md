# MCP Stock Analyzer

A stock analysis tool built with **FastMCP** and **LangGraph**. Exposes market data tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), letting any MCP-compatible host (Cursor, Claude Desktop, etc.) call real-time stock analysis directly from chat.

## What it does

- Fetches **price history**, **financials**, and **news** from [Polygon.io](https://polygon.io)
- Computes **50-day SMA** and technical signals locally
- Runs a **LangGraph agent** that combines all signals into a `BUY / HOLD / SELL` rating with a breakdown of drivers

## Architecture

```
MCP Host (Cursor / Claude Desktop)
    └── FastMCP Server  (mcp_server.py)
            ├── price_history  → Polygon /v2/aggs
            ├── financials     → Polygon /vX/reference/financials
            ├── news           → Polygon /v2/reference/news
            ├── sma            → local computation over price history
            └── short_interest → placeholder (bring your own provider)

LangGraph Agent  (agent.py)
    ├── fetch_all  – calls all MCP tools in parallel
    └── decide     – deterministic scoring → BUY / HOLD / SELL
```

## Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) package manager
- A free [Polygon.io](https://polygon.io) API key

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/aravind1808v/MCP-Stocks.git
cd MCP-Stocks

# 2. Install dependencies
uv sync

# 3. Set your API key
export POLYGON_API_KEY=your_key_here
# or create a .env file:
echo "POLYGON_API_KEY=your_key_here" > .env
```

## Running the MCP server

```bash
uv run python mcp_server.py
```

The server starts and listens for MCP tool calls over stdio.

## Connecting to Cursor

Add this to your Cursor MCP config (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "stock-analyzer": {
      "command": "/path/to/MCP-Stocks/run_cursor_mcp.sh"
    }
  }
}
```

Then restart Cursor. You can now ask things like:

> *"What is the SMA-50 for NVDA?"*
> *"Get me the latest news for TSLA."*
> *"Fetch financials for AAPL for the last 4 quarters."*

## Running the LangGraph agent directly

```bash
uv run python agent.py
```

This runs `analyze_stock("AAPL")` end-to-end and prints a JSON rating object:

```json
{
  "ticker": "AAPL",
  "rating": "BUY",
  "score": 2,
  "drivers": {
    "technical": { "pct_vs_sma_50": 4.2, "signal": "bullish" },
    "fundamentals": "ok",
    "news": { "count": 10, "signal": "mixed" }
  },
  "sources": ["https://..."]
}
```

## Available MCP tools

| Tool | Description | Key params |
|---|---|---|
| `price_history` | Daily OHLCV bars | `ticker`, `days` (default 365) |
| `financials` | Income / balance / cash flow | `ticker`, `limit` (default 4) |
| `news` | Recent news articles | `ticker`, `limit` (default 10) |
| `sma` | Simple moving average | `ticker`, `window` (default 50), `days` |
| `short_interest` | Short interest placeholder | `ticker` |

## Project structure

```
mcp_server.py      – FastMCP server with all market data tools
agent.py           – LangGraph graph: fetch → decide → rating
main.py            – CLI entry point
run_cursor_mcp.sh  – Shell wrapper for Cursor MCP config
pyproject.toml     – Project metadata and dependencies
```

## Extending

- **Better fundamentals scoring** — parse revenue growth, margins, and FCF from the `financials` tool results in `agent.py:decide()`
- **News sentiment** — integrate an NLP model or an LLM call to replace the placeholder `"mixed"` signal
- **Short interest** — wire `short_interest` to a provider like Finviz or a premium Polygon plan
- **LLM summarizer** — replace the deterministic `decide` node with a Claude / GPT call for natural-language analysis

## License

MIT
