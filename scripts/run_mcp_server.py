#!/usr/bin/env python
"""Entry point for MCP server (STDIO mode)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_ontology_mcp.server import OntologyMCPServer


def main() -> None:
    """Run MCP server."""
    try:
        server = OntologyMCPServer()
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
