# MCP Stock Analyzer

A demo project showcasing a **Model Context Protocol (MCP)** server with
**FastMCP + LangGraph**, hosted via **Cursor**.

## Architecture
Chat UI (Cursor)
→ MCP Host
→ FastMCP Server (tools)
→ LangGraph Agent
→ Market data APIs

## Run locally

```bash
uv sync
uv run python mcp_server.py
