# Obsidian Ontology MCP Server

> ⚠️ **EXPERIMENTAL**: This MCP server is in early experimental stages. APIs and features may change significantly. Use in production at your own risk.

A Model Context Protocol (MCP) server that provides fast access to related concepts from your Obsidian knowledge base by extracting SKOS and Schema.org structured metadata.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your vault path and credentials

# Run HTTP server
python scripts/run_http_server.py

# Run MCP server (for OpenCode)
python scripts/run_mcp_server.py
```

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [API Reference](docs/api.md) - MCP tools and HTTP endpoints
- [Deployment Guide](docs/deployment.md) - Production deployment
- [Implementation Status](docs/IMPLEMENTATION.md) - Development progress

## Goal

The primary goal is to enable AI agents to quickly access related concepts from your personal Obsidian knowledge base. By using SKOS (Simple Knowledge Organization System) and Schema.org metadata in your note frontmatter, the server builds a queryable knowledge graph that allows:

- Finding concepts by name or description
- Expanding context around a concept (related, broader, narrower concepts)
- Discovering conceptual paths between ideas
- Retrieving full note content for AI reasoning

## Features

- SKOS/Schema.org metadata extraction from Obsidian frontmatter
- Graph-based knowledge representation using NetworkX
- MCP tools for concept retrieval and context expansion
- Basic authentication and input validation
- Structured audit logging  

## License

MIT License - see LICENSE file for details.
