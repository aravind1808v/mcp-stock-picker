#!/usr/bin/env bash
set -euo pipefail

cd "/Users/aravindveluchamy/Documents/GenAi/MCP-Stocks"
exec "/opt/homebrew/bin/uv" run python mcp_server.py