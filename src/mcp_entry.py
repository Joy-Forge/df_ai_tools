"""Standalone MCP entry point — stdio mode for command-based Agent config.

Usage:
    python src/mcp_entry.py
    # Agent config: "command": "python", "args": ["-m", "src.mcp_entry"]
"""

import sys
sys.path.insert(0, ".")

from src.main import mcp

if __name__ == "__main__":
    mcp.run()
