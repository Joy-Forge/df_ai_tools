"""Standalone MCP entry point — stdio mode for command-based Agent config.

Usage:
    python src/mcp_entry.py
    # Agent config: "command": "python", "args": ["-m", "src.mcp_entry"]
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of CWD
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import mcp

if __name__ == "__main__":
    mcp.run()
