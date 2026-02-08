# Installation & Testing Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dependencies
pip install -e ".[dev]"
```

### 2. Test Extraction (No Server)

```bash
# Test with sample vault
python scripts/test_extraction.py
```

Expected output:
```
============================================================
Obsidian Ontology MCP Server - Test Script
============================================================

1. Extracting concepts from: .../sample_vault
   ✓ Found 3 concepts

   Concepts:
   - Machine Learning (machine_learning)
   - Supervised Learning (supervised_learning)
   - Regression (regression)

2. Building knowledge graph...
   ✓ Graph: 3 nodes, 6 edges

3. Building indexes...
   ✓ Indexed 3 labels

4. Testing query engine...
   a) Search for 'machine learning':
      Found 1 results
      - Machine Learning

   b) Get concept 'regression':
      ✓ Regression
        Definition: Statistical method for modeling relationships between variables
        Broader: ['supervised_learning']
        Narrower: ['linear_regression']

   c) Expand context for 'regression' (depth=2):
      ✓ Focus: Regression
        Direct relations:
          broader: ['Supervised Learning']

   d) Find path from 'regression' to 'machine_learning':
      ✓ Path length: 2
        Path: Regression → Supervised Learning → Machine Learning

5. Graph statistics:
   Total concepts: 3
   Total relations: 6

============================================================
✓ All tests completed successfully!
============================================================
```

### 3. Run MCP Server

```bash
# Run MCP server (STDIO mode for OpenCode)
python scripts/run_mcp_server.py
```

The server will:
1. Extract concepts from vault
2. Build knowledge graph
3. Register MCP tools
4. Listen on STDIO for MCP protocol

## Project Structure

```
mcp-ontobi/
├── src/obsidian_ontology_mcp/
│   ├── config.py                 # Pydantic settings
│   ├── server.py                 # Main server orchestration
│   ├── extraction/               # SKOS extraction pipeline
│   │   ├── parser.py             # Frontmatter parser
│   │   ├── skos_extractor.py    # Concept extractor
│   │   └── schema_mapper.py     # Schema.org mapping
│   ├── graph/                    # Knowledge graph
│   │   ├── builder.py            # Graph construction
│   │   ├── indexer.py            # Multi-index system
│   │   └── query.py              # Query engine
│   ├── mcp/                      # MCP protocol
│   │   └── tools.py              # Tool definitions
│   ├── security/                 # Security layer
│   │   ├── auth.py               # JWT authentication
│   │   ├── validation.py         # Input sanitization
│   │   └── audit.py              # Audit logging
│   └── monitoring/               # File system watcher (TODO)
├── scripts/
│   ├── run_mcp_server.py         # MCP entry point
│   └── test_extraction.py        # Test script
├── tests/fixtures/sample_vault/  # Test Obsidian notes
├── docs/                         # Documentation
├── logs/                         # Log files
├── pyproject.toml                # Project configuration
├── .env                          # Environment configuration
└── README.md                     # Main README
```

## Configuration

The `.env` file contains all configuration. Key settings:

```bash
# Point to your Obsidian vault
VAULT_PATH=/path/to/your/vault

# Optional: Authentication settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...

# Optional: JWT secret
JWT_SECRET_KEY=your_secret_key_here
```

### Generate Secrets

If you plan to use the authentication features:

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate password hash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password'))"
```

## Testing with Your Own Vault

1. Create Obsidian notes with SKOS frontmatter:

```markdown
---
prefLabel: Your Concept
altLabel: [Alternative Name]
definition: Description of the concept
notation: CODE.001

# SKOS Relations
broader: [[Parent Concept]]
narrower: [[Child Concept]]
related: [[Related Concept]]

# Schema.org
type: EducationalMaterial
about: [topic1, topic2]
educationalLevel: graduate
---

# Your Concept

Your note content here...
```

2. Update `.env` with your vault path:

```bash
VAULT_PATH=/path/to/your/obsidian/vault
```

3. Run test script:

```bash
python scripts/test_extraction.py
```

## MCP Tools Available

Once the server is running, these tools are available to AI agents:

1. **get_concept** - Retrieve concept by ID
2. **expand_context** - Gather related concepts (PRIMARY TOOL)
3. **search_concepts** - Search by text
4. **get_concept_path** - Find path between concepts
5. **get_statistics** - Graph metrics

## Known Limitations

- No real-time vault monitoring (requires manual server restart to pick up changes)
- HTTP REST API not fully implemented
- Limited test coverage
- Performance not optimized for large vaults (1000+ notes)

## Troubleshooting

### Import Errors

If you see import errors, ensure you've installed dependencies:

```bash
pip install -e ".[dev]"
```

### Vault Path Not Found

Check that `VAULT_PATH` in `.env` points to an existing directory:

```bash
ls -la $VAULT_PATH
```

### No Concepts Found

Ensure your notes have `prefLabel` in frontmatter. Only notes with `prefLabel` are treated as concepts.

## Documentation

- [Architecture](docs/architecture.md) - System design
- [API Reference](docs/api.md) - MCP tools and HTTP endpoints
- [Deployment Guide](docs/deployment.md) - Production deployment
- [Implementation Status](docs/IMPLEMENTATION.md) - Development progress
