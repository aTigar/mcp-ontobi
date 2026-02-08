# Obsidian Ontology MCP Server

> ⚠️ **EXPERIMENTAL**: Early development. Not recommended for production use.

A Model Context Protocol (MCP) server that provides fast access to related concepts from your Obsidian knowledge base by extracting SKOS and Schema.org structured metadata.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This server extracts SKOS (Simple Knowledge Organization System) and Schema.org metadata from Obsidian markdown frontmatter and builds a queryable knowledge graph. The goal is to enable AI agents to quickly access related concepts from your personal knowledge base.

### What It Does

- Parses SKOS metadata (prefLabel, broader, narrower, related) from Obsidian note frontmatter
- Builds an in-memory graph using NetworkX
- Exposes MCP tools for concept retrieval and context expansion
- Provides basic authentication and input validation

### Current Status

Functional for small to medium vaults with SKOS-annotated notes. Several features are incomplete or not yet implemented.  

## Quick Start

### Prerequisites

- Python 3.11+
- Obsidian vault with notes containing SKOS frontmatter (see [Vault Setup](#vault-setup))
- Basic familiarity with command line and environment variables

### Installation

```bash
# Clone repository
git clone https://github.com/aTigar/mcp-ontobi.git
cd mcp-ontobi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env
nano .env  # Edit with your vault path and credentials
```

### Generate Admin Password

```bash
python -c "
from passlib.context import CryptContext
pwd = 'your_secure_password'
print(CryptContext(schemes=['bcrypt']).hash(pwd))
"
```

Copy the hash to `ADMIN_PASSWORD_HASH` in `.env`.

### Run Server

```bash
# MCP server (for OpenCode)
python scripts/run_mcp_server.py

# Note: HTTP server and dual mode not fully implemented
```

### Test

```bash
# Test extraction with sample vault
python scripts/test_extraction.py
```

## Vault Setup

Your Obsidian notes need SKOS/Schema.org frontmatter:

```markdown
---
# SKOS Core
prefLabel: Regression Analysis
altLabel: [Regression, Regressionsanalyse]
definition: Statistical method for modeling relationships between variables
notation: ML.REG.001
inScheme: ml_concepts

# SKOS Relations
broader: [[Supervised Learning]]
narrower: [[Linear Regression]], [[Logistic Regression]]
related: [[Correlation]], [[Prediction]]

# Schema.org
type: EducationalMaterial
about: [statistics, prediction]
teaches: [linear models, least squares]
educationalLevel: graduate
learningResourceType: concept

# Academic Metadata
course: [ML101, DS202]
lectureWeek: 3
prerequisite: [[Probability Theory]], [[Linear Algebra]]
---

# Regression Analysis

Your note content here...
```

**Minimum required:** `prefLabel` (only notes with this are treated as concepts)

## Usage

### OpenCode Integration

Add to OpenCode MCP configuration:

```json
{
  "mcpServers": {
    "obsidian-ontology": {
      "command": "python",
      "args": ["/absolute/path/to/scripts/run_mcp_server.py"],
      "env": {
        "VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

**Example prompt:**
```
Use expand_context with concept_id='regression' and max_depth=2 
to gather full context before answering questions about regression analysis.
```

### n8n Integration

HTTP REST API not fully implemented. Currently only MCP protocol is supported.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Clients (OpenCode, n8n, MCP clients)               │
└──────────────┬──────────────────────────────────────┘
               │ MCP (STDIO) / HTTP (JWT)
┌──────────────▼──────────────────────────────────────┐
│  Transport Layer (FastMCP + FastAPI)                │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Security (JWT, Rate Limit, Sanitization, Audit)    │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  MCP Tools (get_concept, expand_context, search)    │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Knowledge Graph (NetworkX/igraph)                  │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Extraction Pipeline (SKOS + Schema.org)            │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Obsidian Vault (Markdown + Frontmatter)            │
└─────────────────────────────────────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed documentation.

## MCP Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `get_concept` | Retrieve concept by ID | Lookup specific concept |
| `expand_context` | Gather related concepts | AI context building |
| `search_concepts` | Full-text search | Find concepts by keywords |
| `get_concept_path` | Find relation path | Understand conceptual links |
| `get_statistics` | Graph metrics | Monitoring, health checks |

See [docs/api.md](docs/api.md) for complete API documentation.

## Security

Basic security features are implemented:

- JWT authentication with bcrypt password hashing
- Input validation to prevent basic injection attacks
- Rate limiting configuration
- Audit logging

Note: Not audited for production use. Review and test before deploying in sensitive environments.

## Configuration

### Environment Variables

```bash
# Core
VAULT_PATH=/path/to/vault         # Required
VAULT_WATCH_ENABLED=true          # Auto-update on changes

# Authentication
ENABLE_AUTHENTICATION=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt>      # Generate with script above

# JWT
JWT_SECRET_KEY=<auto-generated>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Security Limits
MAX_CONTEXT_DEPTH=3
MAX_RESULTS_PER_QUERY=100

# HTTP
HTTP_HOST=127.0.0.1               # Localhost only (secure)
HTTP_PORT=8000
HTTP_ENABLE_CORS=false            # Disabled by default

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ontology_mcp.log
AUDIT_LOG_FILE=logs/audit.log
```

See [.env.example](.env.example) for full configuration.

## Project Structure

```
obsidian-ontology-mcp/
├── src/obsidian_ontology_mcp/
│   ├── config.py              # Pydantic settings
│   ├── server.py              # Main server
│   ├── extraction/            # SKOS extraction
│   │   ├── parser.py          # Frontmatter parser
│   │   ├── skos_extractor.py  # Concept extraction
│   │   └── schema_mapper.py   # Schema.org mapping
│   ├── graph/                 # Knowledge graph
│   │   ├── builder.py         # Graph construction
│   │   ├── indexer.py         # Multi-index system
│   │   └── query.py           # Query engine
│   ├── mcp/                   # MCP protocol
│   │   ├── tools.py           # Tool definitions
│   │   └── resources.py       # Resource definitions
│   ├── http/                  # HTTP server
│   │   └── routes.py          # FastAPI endpoints
│   ├── security/              # Security layer
│   │   ├── auth.py            # JWT authentication
│   │   ├── validation.py      # Input sanitization
│   │   ├── rate_limit.py      # Rate limiting
│   │   └── audit.py           # Audit logging
│   └── monitoring/
│       └── watcher.py         # File system watcher
├── scripts/
│   ├── run_mcp_server.py      # MCP entry point
│   ├── run_http_server.py     # HTTP entry point
│   └── run_dual_server.py     # Both servers
├── tests/
│   ├── test_extraction.py
│   ├── test_graph.py
│   ├── test_mcp_tools.py
│   └── test_security.py
├── docs/
│   ├── architecture.md        # System architecture
│   ├── api.md                 # API documentation
│   └── deployment.md          # Deployment guide
├── pyproject.toml             # Project config
├── .env.example               # Example configuration
└── README.md                  # This file
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code formatting
black src/ tests/

# Linting
ruff check src/

# Type checking
mypy src/

# Security scan
bandit -r src/
safety check
```

### Adding New Tools

1. Define tool in `src/obsidian_ontology_mcp/mcp/tools.py`
2. Add decorator `@mcp.tool()`
3. Include in `allowed_tools` config
4. Tool auto-discovered by MCP clients

### Adding Schema.org Properties

1. Update `ConceptMetadata` model in `extraction/parser.py`
2. Add fields to frontmatter example
3. Properties available in graph nodes

## Performance

Performance has not been systematically benchmarked. The server uses NetworkX for graph operations, which should handle small to medium vaults (hundreds to low thousands of concepts) adequately. Very large vaults may experience slow startup times or high memory usage.

## Troubleshooting

### Common Issues

**Server won't start**
```bash
tail -50 logs/ontology_mcp.log
```
Check vault path exists, port available, dependencies installed.

**Authentication failures**
```bash
# Regenerate password hash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('new_password'))"
```

**Slow context expansion**
- Reduce `max_depth` to 1 or 2
- Switch to igraph for large vaults
- Enable caching: `GRAPH_CACHE_ENABLED=true`

See [docs/deployment.md#troubleshooting](docs/deployment.md#troubleshooting) for detailed guide.

## Monitoring

### Health Checks

```bash
curl http://127.0.0.1:8000/health
```

### Audit Logs

```bash
# View recent API calls
tail -f logs/audit.log | jq

# Count calls per user
grep tool_call logs/audit.log | jq -r '.username' | sort | uniq -c

# Find authentication failures
grep '"success": false' logs/audit.log
```

### Performance Monitoring

```bash
# Graph statistics
curl http://127.0.0.1:8000/api/statistics

# Memory usage
ps aux | grep run_http_server | awk '{print $6/1024 " MB"}'
```

## Deployment

This is experimental software. Deployment configuration for production environments has not been tested. See [docs/deployment.md](docs/deployment.md) for deployment notes.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- **Python 3.11+** with type hints
- **Black** formatting (88 char line length)
- **Ruff** linting
- **pytest** for tests (>80% coverage)
- **Docstrings** for all public functions

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastMCP - MCP protocol implementation
- SKOS - W3C Simple Knowledge Organization System
- Schema.org - Structured data vocabulary  
- NetworkX - Graph library for Python
