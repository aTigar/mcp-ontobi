# Obsidian Ontology MCP Server - Architecture Documentation

## System Overview

The Obsidian Ontology MCP Server is a production-grade Model Context Protocol (MCP) server that extracts SKOS (Simple Knowledge Organization System) and Schema.org metadata from Obsidian markdown notes to create a queryable knowledge graph. It provides both MCP tools for AI agents (like OpenCode) and HTTP REST APIs for automation workflows (like n8n).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   OpenCode   │  │     n8n      │  │  Other MCP   │          │
│  │  (AI Agent)  │  │  (Workflows) │  │   Clients    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         │ MCP (STDIO)     │ HTTP+JWT         │ MCP              │
└─────────┼─────────────────┼──────────────────┼───────────────────┘
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼───────────────────┐
│                    Transport Layer                                │
│  ┌────────────────────┐  ┌─────────────────────────────┐         │
│  │   FastMCP Server   │  │   FastAPI HTTP Server       │         │
│  │   (STDIO)          │  │   (Uvicorn/ASGI)            │         │
│  └────────────────────┘  └─────────────────────────────┘         │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                    Security Middleware                            │
│  • JWT Authentication (HTTP only)                                 │
│  • Input Sanitization (prompt injection prevention)              │
│  • Rate Limiting (per-user, per-endpoint)                        │
│  • Authorization (RBAC - tool-level permissions)                 │
│  • Audit Logging (structured JSON logs)                          │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                    Business Logic Layer                           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    MCP Tools                              │    │
│  │  • get_concept()       - Retrieve concept by ID          │    │
│  │  • expand_context()    - Context expansion for AI        │    │
│  │  • search_concepts()   - Search by label/definition      │    │
│  │  • get_concept_path()  - Find relation paths             │    │
│  │  • get_statistics()    - Graph metrics                   │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                    Data Access Layer                              │
│  ┌────────────────────┐  ┌─────────────────────────────┐         │
│  │  GraphQueryEngine  │  │     Multi-Index System      │         │
│  │  • Context expand  │  │  • Label index (exact)      │         │
│  │  • Path finding    │  │  • Notation index (codes)   │         │
│  │  • Search          │  │  • Relation index (quick)   │         │
│  └────────────────────┘  └─────────────────────────────┘         │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                    Knowledge Graph Layer                          │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │          NetworkX DiGraph (or igraph for >10k)          │     │
│  │                                                          │     │
│  │  Nodes: SKOS Concepts with attributes                   │     │
│  │  Edges: SKOS Relations (broader/narrower/related)       │     │
│  │                                                          │     │
│  │  Optional: RDFLib for full RDF/SKOS compliance          │     │
│  └─────────────────────────────────────────────────────────┘     │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                   Extraction Pipeline                             │
│  ┌────────────────────┐  ┌─────────────────────────────┐         │
│  │ FrontmatterParser  │  │   SKOSExtractor             │         │
│  │ • YAML parsing     │  │   • Concept creation        │         │
│  │ • Pydantic valid.  │  │   • Wikilink resolution     │         │
│  └────────────────────┘  └─────────────────────────────┘         │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────┐
│                   File System Layer                               │
│  ┌────────────────────┐  ┌─────────────────────────────┐         │
│  │   VaultWatcher     │  │   Obsidian Vault            │         │
│  │   (Watchdog)       │  │   (Markdown Files)          │         │
│  │  • File events     │  │   • SKOS frontmatter        │         │
│  │  • Debouncing      │  │   • Schema.org metadata     │         │
│  │  • Incremental     │  │   • Note content            │         │
│  └────────────────────┘  └─────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Transport Layer

#### FastMCP Server (STDIO)
- **Purpose**: MCP protocol implementation for AI agents
- **Transport**: STDIO (Standard Input/Output)
- **Use Case**: OpenCode, Claude Desktop, other MCP clients
- **Features**:
  - Tool registration and discovery
  - JSON-RPC 2.0 protocol
  - Process-isolated execution
  - No authentication needed (process isolation provides security)

#### FastAPI HTTP Server (Uvicorn)
- **Purpose**: REST API for automation workflows
- **Transport**: HTTP/HTTPS with JWT authentication
- **Use Case**: n8n workflows, webhooks, custom integrations
- **Features**:
  - JWT token authentication
  - Rate limiting per endpoint
  - CORS with strict origin whitelist
  - Structured audit logging

### 2. Security Middleware

#### Authentication
- **HTTP**: JWT (JSON Web Tokens) with HS256 algorithm
- **MCP**: Process isolation (no shared memory between clients)
- **Password Hashing**: bcrypt with salt
- **Token Expiration**: Configurable (default 30 minutes)

#### Input Sanitization
- **Prompt Injection Prevention**: Pattern-based blocking
- **XSS Prevention**: HTML entity escaping
- **Path Traversal**: Blocked patterns
- **SQL Injection**: Blocked patterns (though no SQL used)
- **Length Limits**: Configurable max query/content lengths

#### Rate Limiting
- **Strategy**: Token bucket per user/IP
- **Limits**: Configurable per minute (default: 60 req/min)
- **Burst**: Configurable burst allowance (default: 10)
- **Storage**: In-memory (Redis for distributed deployment)

#### Authorization (RBAC)
- **Levels**: Tool-level permissions
- **Current**: All authenticated users access all tools
- **Extensible**: Role-based tool access easy to add

#### Audit Logging
- **Format**: Structured JSON (SIEM-ready)
- **Events Logged**:
  - Authentication attempts (success/failure)
  - Tool executions (with parameters)
  - Rate limit violations
  - Validation errors
  - API errors
- **Destinations**: File (configurable path)

### 3. Business Logic Layer

#### MCP Tools

##### `get_concept(concept_id, include_relations)`
- Retrieve single concept by ID or prefLabel
- Returns: Concept metadata with optional relations
- Security: Input sanitization, authorization check

##### `expand_context(concept_id, relation_types, max_depth, include_content)`
- **Primary tool for AI agents**
- Expands context around concept via graph traversal
- Returns: Focus concept + all related concepts with content
- Security: Depth limits, content size limits
- Use Case: Gather full context before AI reasoning

##### `search_concepts(query, limit)`
- Full-text search across labels and definitions
- Returns: List of matching concepts
- Security: Result limit, input sanitization

##### `get_concept_path(from_concept, to_concept)`
- Find shortest path between two concepts
- Returns: Ordered list of concepts in path
- Use Case: Understand conceptual relationships

##### `get_statistics()`
- Graph metrics and system info
- Returns: Node count, edge count, vault path, version
- Use Case: Monitoring, health checks

### 4. Data Access Layer

#### GraphQueryEngine
- **Purpose**: Query abstraction over knowledge graph
- **Methods**:
  - `expand_context()`: BFS traversal with relation filtering
  - `search_concepts()`: Text-based search
  - `get_related_concepts()`: Direct relation lookup
- **Optimization**: Uses multi-index system for O(1) lookups

#### Multi-Index System
```python
{
  "label_index": {
    "en": {"regression": "concept_id_1"},
    "de": {"regression": "concept_id_1"},
    "alt": {"least squares": "concept_id_1"}
  },
  "notation_index": {
    "ML.REG.001": "concept_id_1"
  },
  "relation_index": {
    "broader": {"concept_id_1": ["concept_id_2"]},
    "narrower": {"concept_id_2": ["concept_id_1"]}
  }
}
```

### 5. Knowledge Graph Layer

#### NetworkX DiGraph
- **Default**: For vaults <10,000 concepts
- **Structure**: Directed graph with attributes on nodes/edges
- **Nodes**: SKOS concepts with full metadata
- **Edges**: Relations (skos:broader, skos:narrower, skos:related)
- **Memory**: ~50KB per 100 concepts (approximate)

#### igraph (Optional)
- **Use When**: Vault >10,000 concepts
- **Advantage**: 10x faster, 3x less memory (C-based)
- **Trade-off**: Less Pythonic API
- **Switch**: Configuration flag in settings

#### RDFLib (Optional)
- **Purpose**: Full SKOS/RDF compliance
- **Use Case**: Export to RDF, SPARQL queries
- **Trade-off**: Slower, more memory

### 6. Extraction Pipeline

#### FrontmatterParser
- **Input**: Markdown file path
- **Process**:
  1. Parse YAML frontmatter (python-frontmatter)
  2. Validate with Pydantic model
  3. Extract note body content
- **Output**: ConceptMetadata object
- **Error Handling**: Logs errors, returns None for invalid files

#### SKOSExtractor
- **Input**: Vault path
- **Process**:
  1. Recursively find all .md files
  2. Parse each file with FrontmatterParser
  3. Filter: Only files with prefLabel are concepts
  4. Create SKOSConcept objects
- **Output**: List of SKOSConcept objects
- **Incremental**: Single-file extraction for updates

#### Wikilink Resolution
- **Pattern**: `[[Note Title]]` or `[[Note Title|Alias]]`
- **Resolution**: Note title → concept_id (lowercase, underscores)
- **Handles**: Lists, inline text, bidirectional links

### 7. File System Layer

#### VaultWatcher (Watchdog)
- **Events Monitored**: create, modify, delete
- **Filters**: Only .md files, exclude hidden/dotfiles
- **Debouncing**: 1-second delay to avoid rapid-fire events
- **Actions**:
  - **create/modify**: Re-extract concept, update graph
  - **delete**: Remove concept from graph
- **Threading**: Background thread, non-blocking

## Data Flow

### Initial Startup
```
1. Load configuration from .env
2. Initialize security (JWT keys, password hashes)
3. Scan vault: Extract all SKOS concepts
4. Build knowledge graph: Add nodes and edges
5. Build indexes: Label, notation, relation
6. Register MCP tools with FastMCP
7. Start file watcher (if enabled)
8. Start HTTP server (background thread)
9. Start MCP server (main thread, STDIO)
```

### MCP Tool Call Flow (OpenCode)
```
1. OpenCode sends MCP tool call → STDIO
2. FastMCP receives JSON-RPC request
3. Security: Sanitize inputs, validate parameters
4. Tool function executes:
   a. Query GraphQueryEngine
   b. Traverse graph if needed
   c. Apply result limits
5. Audit: Log tool call (user, params, duration)
6. Return: JSON response → STDIO → OpenCode
```

### HTTP API Call Flow (n8n)
```
1. n8n sends HTTP POST with JWT
2. FastAPI middleware: Verify JWT token
3. Rate limiting: Check user quota
4. Input validation: Sanitize request body
5. Route handler executes:
   a. Query GraphQueryEngine
   b. Apply security limits
6. Audit: Log API call (user, endpoint, status)
7. Return: JSON response → n8n
```

### File Change Flow
```
1. User edits note.md in Obsidian
2. VaultWatcher detects 'modified' event
3. Debounce: Wait 1 second for additional changes
4. Extract: Re-parse note with FrontmatterParser
5. Update graph:
   a. Remove old edges
   b. Update node attributes
   c. Add new edges based on updated relations
6. Update indexes:
   a. Label index
   b. Relation index
7. Graph ready: Next query reflects changes
```

## Scalability Considerations

### Small Vaults (<1,000 concepts)
- **Graph**: NetworkX (Python-based)
- **Search**: In-memory linear scan
- **Startup**: <1 second
- **Memory**: ~50MB

### Medium Vaults (1,000-10,000 concepts)
- **Graph**: NetworkX with indexes
- **Search**: Indexed lookups
- **Startup**: 2-5 seconds
- **Memory**: ~500MB

### Large Vaults (>10,000 concepts)
- **Graph**: Switch to igraph (C-based)
- **Search**: Add Whoosh or FAISS for semantic search
- **Startup**: 5-15 seconds
- **Memory**: ~1-2GB
- **Considerations**:
  - Lazy loading for content
  - Pagination for large results
  - Graph partitioning for distributed

## Security Architecture

### Defense in Depth

1. **Network Layer**: Localhost-only binding (127.0.0.1)
2. **Transport Layer**: TLS (via nginx reverse proxy for remote)
3. **Application Layer**: JWT authentication, CORS restrictions
4. **Input Layer**: Sanitization, validation, pattern blocking
5. **Business Logic Layer**: Authorization (RBAC), rate limiting
6. **Data Layer**: Read-only graph (no write operations exposed)
7. **Audit Layer**: Structured logging for forensics

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| Prompt Injection | Pattern blocking, input sanitization |
| DoS (Rate-based) | Rate limiting (per user/IP) |
| DoS (Resource) | Result size limits, depth limits, timeouts |
| Credential Theft | bcrypt hashing, JWT expiration |
| XSS | HTML entity escaping |
| CSRF | CORS restrictions, JWT (not cookies) |
| MITM | TLS (via nginx for remote access) |
| Path Traversal | Input validation, blocked patterns |

### Security Configuration

All security settings in `.env`:
```bash
# Authentication
ENABLE_AUTHENTICATION=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt hash>

# JWT
JWT_SECRET_KEY=<random 32-byte key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Input Validation
MAX_QUERY_LENGTH=1000
MAX_CONTEXT_DEPTH=3
MAX_RESULTS_PER_QUERY=100
MAX_CONCEPT_CONTENT_LENGTH=50000

# CORS
HTTP_ENABLE_CORS=false
HTTP_ALLOWED_ORIGINS=["http://localhost:5678"]
```

## Deployment Architecture

### Local Development
```
┌──────────────────────────────────────┐
│      Developer Machine (Leipzig)     │
│                                       │
│  ┌────────────────────────────────┐  │
│  │  Obsidian Vault                │  │
│  │  /home/user/obsidian/ml-vault  │  │
│  └────────────────────────────────┘  │
│                │                      │
│  ┌─────────────▼──────────────────┐  │
│  │  MCP Server                    │  │
│  │  127.0.0.1:8000 (HTTP)         │  │
│  │  STDIO (MCP)                   │  │
│  └─────────────┬──────────────────┘  │
│                │                      │
│  ┌─────────────▼──────────────────┐  │
│  │  OpenCode (STDIO)              │  │
│  │  n8n (HTTP localhost)          │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### Production (Remote Access)
```
┌──────────────────────────────────────────────┐
│            Internet                           │
└───────────────┬──────────────────────────────┘
                │ HTTPS (443)
┌───────────────▼──────────────────────────────┐
│      Nginx Reverse Proxy                      │
│  • TLS termination (Let's Encrypt)           │
│  • Rate limiting (nginx level)               │
│  • Security headers                          │
│  • Access logs                               │
└───────────────┬──────────────────────────────┘
                │ HTTP (localhost)
┌───────────────▼──────────────────────────────┐
│      MCP Server (127.0.0.1:8000)             │
│  • JWT authentication                        │
│  • Application rate limiting                 │
│  • Audit logging                             │
└───────────────┬──────────────────────────────┘
                │
┌───────────────▼──────────────────────────────┐
│      Obsidian Vault (Read-Only)              │
└──────────────────────────────────────────────┘
```

## Technology Stack Summary

| Layer | Technology | Reason |
|-------|-----------|---------|
| MCP Framework | FastMCP | 5x faster dev than vanilla SDK |
| HTTP Framework | FastAPI | Type safety, OpenAPI, async |
| ASGI Server | Uvicorn | High performance, HTTP/2 |
| Graph Library | NetworkX / igraph | NetworkX: ease, igraph: speed |
| Validation | Pydantic v2 | Type safety, validation |
| Authentication | JWT (python-jose) | Stateless, standard |
| Password Hash | bcrypt (passlib) | Industry standard |
| Rate Limiting | SlowAPI | FastAPI-native |
| File Watching | Watchdog | Cross-platform |
| Logging | structlog | Structured, SIEM-ready |
| Testing | pytest | Python standard |

## Configuration Management

### Environment Variables (.env)
- All configuration externalized
- No secrets in code
- Validation via Pydantic Settings
- Type checking for all config values

### Secrets Management
- JWT secret: Auto-generated if not provided
- Admin password: Must be bcrypt hash
- Never commit .env to version control

### Logging Configuration
```python
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/server.log
AUDIT_LOG_FILE=logs/audit.log
```

## Monitoring & Observability

### Health Checks
- **Endpoint**: `/health`
- **Returns**: Status, version, vault path
- **Use**: Kubernetes liveness probe, uptime monitoring

### Metrics Available
- Total concepts in graph
- Total relations (edges)
- Server uptime
- Request rate (via audit logs)

### Audit Trail
All events logged in structured JSON:
```json
{
  "timestamp": "2026-02-08T20:15:00Z",
  "event_type": "tool_call",
  "username": "admin",
  "details": {
    "tool_name": "expand_context",
    "arguments": {"concept_id": "regression", "max_depth": 2},
    "success": true,
    "execution_time_ms": 45.2
  }
}
```

### Log Aggregation
- Use ELK Stack (Elasticsearch, Logstash, Kibana)
- Or Grafana Loki
- Or CloudWatch (if on AWS)

## Extensibility Points

### Adding New Tools
1. Define tool function in `mcp/tools.py`
2. Add decorator `@mcp.tool()`
3. Include in `allowed_tools` config
4. Tool auto-appears in MCP discovery

### Adding New Relation Types
1. Update frontmatter schema
2. Add relation type to `SKOSExtractor`
3. Update `GraphQueryEngine` traversal
4. No code changes needed in tools

### Adding Custom Indexes
1. Implement index class in `graph/indexer.py`
2. Build during graph initialization
3. Query in `GraphQueryEngine`

### Adding Schema.org Types
1. Update `ConceptMetadata` model
2. Add fields to frontmatter parser
3. Include in graph node attributes
4. Query via existing tools

## Performance Benchmarks

### Extraction (Initial Load)
- 100 concepts: ~0.2s
- 1,000 concepts: ~2s
- 10,000 concepts: ~25s (NetworkX) / ~5s (igraph)

### Query Performance
- `get_concept()`: <1ms (indexed lookup)
- `search_concepts()`: 5-50ms (linear scan)
- `expand_context(depth=2)`: 10-100ms (BFS traversal)
- `get_concept_path()`: 20-200ms (shortest path)

### Memory Usage
- Base server: ~50MB
- + 1,000 concepts: ~100MB
- + 10,000 concepts: ~600MB (NetworkX) / ~200MB (igraph)

### Concurrent Requests
- HTTP: 100+ req/sec (single process)
- MCP: 1 client per process (by design)

## Next Steps for Production

1. **Add semantic search**: Use sentence-transformers + FAISS
2. **Add caching layer**: Redis for frequently accessed concepts
3. **Add graph analytics**: PageRank, community detection
4. **Add SPARQL endpoint**: RDFLib query interface
5. **Add GraphQL API**: Alternative to REST
6. **Add WebSocket support**: Real-time updates
7. **Add Docker deployment**: Container orchestration
8. **Add CI/CD pipeline**: Automated testing and deployment
