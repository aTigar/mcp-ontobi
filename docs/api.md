# API Documentation - Obsidian Ontology MCP Server

## Overview

This document describes both the MCP tools and HTTP REST API endpoints provided by the Obsidian Ontology MCP Server.

## MCP Tools API

MCP tools are accessed via the Model Context Protocol (STDIO transport) by AI agents like OpenCode and Claude Desktop.

### Tool: `get_concept`

Retrieve a single SKOS concept by ID or preferred label.

**Input Schema:**
```json
{
  "concept_id": "string (required)",
  "include_relations": "boolean (optional, default: true)"
}
```

**Example Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_concept",
    "arguments": {
      "concept_id": "regression",
      "include_relations": true
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "id": "regression",
  "prefLabel": "Regression Analysis",
  "definition": "Statistical method for modeling relationships between variables",
  "notation": "ML.REG.001",
  "file_path": "/path/to/vault/concepts/regression.md",
  "schema": {
    "type": "EducationalMaterial",
    "about": ["statistics", "prediction"],
    "educationalLevel": "graduate"
  },
  "broader": ["supervised_learning"],
  "narrower": ["linear_regression", "logistic_regression"],
  "related": ["correlation", "prediction"]
}
```

**Error Response:**
```json
{
  "error": "Concept 'xyz' not found",
  "available_count": 1247
}
```

---

### Tool: `expand_context`

**PRIMARY TOOL** - Expand context around a concept for AI agent reasoning.

This tool performs graph traversal to gather all related concepts and their full content, providing comprehensive context to AI agents for accurate reasoning.

**Input Schema:**
```json
{
  "concept_id": "string (required)",
  "relation_types": "array[string] (optional, default: ['broader', 'narrower', 'related'])",
  "max_depth": "integer (optional, default: 2, max: 3)",
  "include_content": "boolean (optional, default: true)"
}
```

**Example Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "expand_context",
    "arguments": {
      "concept_id": "regression",
      "relation_types": ["broader", "narrower", "related"],
      "max_depth": 2,
      "include_content": true
    }
  },
  "id": 2
}
```

**Response:**
```json
{
  "focus_concept": {
    "id": "regression",
    "uri": "vault://concepts#regression",
    "prefLabel": "Regression Analysis",
    "definition": "Statistical method for modeling relationships...",
    "file_path": "/path/to/vault/concepts/regression.md",
    "content": "# Regression Analysis\n\nRegression is a statistical method..."
  },
  "direct_relations": {
    "broader": [
      {
        "id": "supervised_learning",
        "prefLabel": "Supervised Learning",
        "definition": "ML paradigm with labeled training data"
      }
    ],
    "narrower": [
      {
        "id": "linear_regression",
        "prefLabel": "Linear Regression"
      },
      {
        "id": "logistic_regression",
        "prefLabel": "Logistic Regression"
      }
    ],
    "related": [
      {
        "id": "correlation",
        "prefLabel": "Correlation"
      }
    ]
  },
  "transitive_relations": {
    "broader": [
      {
        "id": "machine_learning",
        "prefLabel": "Machine Learning"
      }
    ],
    "narrower": []
  },
  "context_notes": [
    {
      "id": "supervised_learning",
      "label": "Supervised Learning",
      "content": "# Supervised Learning\n\nSupervised learning is...",
      "file_path": "/path/to/vault/concepts/supervised_learning.md"
    },
    {
      "id": "linear_regression",
      "label": "Linear Regression",
      "content": "# Linear Regression\n\nLinear regression uses...",
      "file_path": "/path/to/vault/concepts/linear_regression.md"
    }
  ]
}
```

**Use Case in AI Prompts:**
```
Before answering questions about regression analysis, use the expand_context 
tool with concept_id='regression' and max_depth=2 to gather:
- Parent concepts (what regression belongs to)
- Child concepts (types of regression)
- Related concepts (associated methods)
- Full note content for all related concepts

This provides complete context for accurate explanations.
```

---

### Tool: `search_concepts`

Search for concepts by label or definition.

**Input Schema:**
```json
{
  "query": "string (required)",
  "limit": "integer (optional, default: 10, max: 100)"
}
```

**Example Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_concepts",
    "arguments": {
      "query": "neural network",
      "limit": 5
    }
  },
  "id": 3
}
```

**Response:**
```json
{
  "query": "neural network",
  "count": 3,
  "results": [
    {
      "id": "neural_network",
      "uri": "vault://concepts#neural_network",
      "prefLabel": "Neural Network",
      "definition": "Computing system inspired by biological neural networks",
      "file_path": "/path/to/vault/concepts/neural_network.md"
    },
    {
      "id": "convolutional_neural_network",
      "prefLabel": "Convolutional Neural Network",
      "definition": "Neural network with convolutional layers",
      "file_path": "/path/to/vault/concepts/cnn.md"
    },
    {
      "id": "recurrent_neural_network",
      "prefLabel": "Recurrent Neural Network",
      "definition": "Neural network with feedback connections",
      "file_path": "/path/to/vault/concepts/rnn.md"
    }
  ]
}
```

---

### Tool: `get_concept_path`

Find the shortest path between two concepts in the knowledge graph.

**Input Schema:**
```json
{
  "from_concept": "string (required)",
  "to_concept": "string (required)"
}
```

**Example Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_concept_path",
    "arguments": {
      "from_concept": "linear_regression",
      "to_concept": "machine_learning"
    }
  },
  "id": 4
}
```

**Response:**
```json
{
  "from": "linear_regression",
  "to": "machine_learning",
  "length": 2,
  "path": [
    {
      "id": "linear_regression",
      "prefLabel": "Linear Regression"
    },
    {
      "id": "regression",
      "prefLabel": "Regression Analysis"
    },
    {
      "id": "supervised_learning",
      "prefLabel": "Supervised Learning"
    },
    {
      "id": "machine_learning",
      "prefLabel": "Machine Learning"
    }
  ]
}
```

**No Path Found:**
```json
{
  "from": "linear_regression",
  "to": "blockchain",
  "path": null,
  "message": "No path found between concepts"
}
```

---

### Tool: `get_statistics`

Get knowledge graph statistics and server information.

**Input Schema:**
```json
{}
```

**Example Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_statistics",
    "arguments": {}
  },
  "id": 5
}
```

**Response:**
```json
{
  "total_concepts": 1247,
  "total_relations": 3891,
  "vault_path": "/home/user/obsidian/ml-vault",
  "server_version": "0.2.0"
}
```

---

## HTTP REST API

HTTP endpoints are accessed via HTTPS with JWT authentication, primarily for n8n workflows and webhook integrations.

### Base URL

```
http://127.0.0.1:8000
```

For remote access (production):
```
https://your-domain.com
```

### Authentication

#### 1. Login to Get JWT Token

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_secure_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Rate Limit:** 5 requests per minute per IP

**Status Codes:**
- `200 OK` - Authentication successful
- `401 Unauthorized` - Invalid credentials
- `429 Too Many Requests` - Rate limit exceeded

#### 2. Use JWT Token in Requests

Include the token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Endpoints

#### Health Check

**Endpoint:** `GET /health`

**Authentication:** Not required

**Request:**
```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "server": "Obsidian Ontology Server",
  "version": "0.2.0"
}
```

---

#### Get Concept

**Endpoint:** `POST /api/concept`

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "concept_id": "regression",
  "include_relations": true
}
```

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/concept \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "concept_id": "regression",
    "include_relations": true
  }'
```

**Response:** Same as MCP `get_concept` tool

**Status Codes:**
- `200 OK` - Concept found
- `401 Unauthorized` - Missing or invalid JWT
- `404 Not Found` - Concept not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

#### Expand Context

**Endpoint:** `POST /api/context/expand`

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "concept_id": "regression",
  "relation_types": ["broader", "narrower", "related"],
  "max_depth": 2,
  "include_content": true
}
```

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/context/expand \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "concept_id": "regression",
    "max_depth": 2,
    "include_content": true
  }'
```

**Response:** Same as MCP `expand_context` tool

**Use Case in n8n:**
```
Workflow: AI Research Assistant
1. HTTP Request Node → /api/context/expand
2. Extract context_notes from response
3. OpenAI Node → Use context as system prompt
4. Return enriched AI response
```

---

#### Search Concepts

**Endpoint:** `POST /api/search`

**Authentication:** Required (JWT)

**Request Body:**
```json
{
  "query": "neural network",
  "limit": 10
}
```

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural network",
    "limit": 10
  }'
```

**Response:** Same as MCP `search_concepts` tool

---

#### Get Statistics

**Endpoint:** `GET /api/statistics`

**Authentication:** Required (JWT)

**Request:**
```bash
curl http://127.0.0.1:8000/api/statistics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:** Same as MCP `get_statistics` tool

---

## Rate Limits

| Endpoint | Limit | Burst |
|----------|-------|-------|
| `/api/auth/login` | 5/minute | 2 |
| `/health` | 100/minute | 20 |
| All other `/api/*` | 60/minute | 10 |

Rate limits are per authenticated user (JWT) or per IP address (unauthenticated).

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1644339600
```

**Rate Limit Exceeded Response:**
```json
{
  "error": "Rate limit exceeded",
  "detail": "60 per 1 minute"
}
```

---

## Error Responses

All errors follow consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| `400 Bad Request` | Invalid input (validation error) |
| `401 Unauthorized` | Missing or invalid JWT token |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Concept not found |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error (check logs) |
| `503 Service Unavailable` | Server not initialized |

---

## Security Considerations

### Input Validation

All inputs are validated and sanitized:
- **Maximum query length**: 1,000 characters
- **Maximum depth**: 3 levels
- **Maximum results**: 100 items
- **Maximum content length**: 50,000 characters per note
- **Blocked patterns**: Prompt injection, XSS, path traversal

### Content Security

Large content is automatically truncated:
```json
{
  "content": "First 50,000 characters of content...\n[... content truncated ...]"
}
```

### Authentication Security

- JWT tokens expire after 30 minutes (configurable)
- Passwords hashed with bcrypt (12 rounds)
- Login attempts rate-limited (5/minute)
- All auth events logged to audit trail

### CORS Policy

CORS is disabled by default. When enabled, only specified origins are allowed:
```python
# In .env
HTTP_ENABLE_CORS=true
HTTP_ALLOWED_ORIGINS=["http://localhost:5678"]  # n8n
```

---

## OpenCode Integration

### Configuration

Add to OpenCode MCP configuration:
```json
{
  "mcpServers": {
    "obsidian-ontology": {
      "command": "python",
      "args": ["/absolute/path/to/scripts/run_mcp_server.py"],
      "env": {
        "VAULT_PATH": "/path/to/obsidian/vault"
      }
    }
  }
}
```

### Example Usage in Prompts

```
System Prompt:
You have access to an academic knowledge base via MCP tools.

Before answering questions:
1. Use search_concepts to find relevant concepts
2. Use expand_context to gather full context
3. Use get_concept_path to understand relationships

Example:
User: "Explain the relationship between linear regression and machine learning"

Steps:
1. search_concepts("linear regression") → find concept_id
2. expand_context(concept_id="linear_regression", max_depth=3)
3. get_concept_path("linear_regression", "machine_learning")
4. Answer using gathered context
```

---

## n8n Integration

### Workflow Example: Context-Aware AI Chat

```
┌─────────────────┐
│  Webhook Trigger│
│  (User Question)│
└────────┬────────┘
         │
┌────────▼────────┐
│  HTTP Request   │
│  POST /api/     │
│  context/expand │
└────────┬────────┘
         │
┌────────▼────────┐
│  Function Node  │
│  Build Prompt   │
│  with Context   │
└────────┬────────┘
         │
┌────────▼────────┐
│  OpenAI Node    │
│  GPT-4 with     │
│  Context        │
└────────┬────────┘
         │
┌────────▼────────┐
│  Return Response│
└─────────────────┘
```

### HTTP Request Node Configuration

**Method:** POST  
**URL:** `http://127.0.0.1:8000/api/context/expand`  
**Authentication:** Generic Credential Type
- **Credential for Generic Authentication:**
  - Credential Type: Header Auth
  - Name: Authorization
  - Value: `Bearer YOUR_JWT_TOKEN`

**Body:**
```json
{
  "concept_id": "{{ $json.concept_id }}",
  "max_depth": 2,
  "include_content": true
}
```

**Response Extraction (Function Node):**
```javascript
// Extract context notes
const contextNotes = $input.item.json.context_notes;

// Build context string
const contextText = contextNotes
  .map(note => `## ${note.label}\n\n${note.content}`)
  .join('\n\n---\n\n');

// Build enriched prompt
return {
  json: {
    system_prompt: `You are an expert on machine learning. Use this context:\n\n${contextText}`,
    user_question: $input.item.json.user_question
  }
};
```

---

## Pagination (Future)

Currently all results returned in single response. For large result sets, future versions will support pagination:

```json
{
  "query": "machine learning",
  "count": 250,
  "page": 1,
  "per_page": 50,
  "total_pages": 5,
  "results": [...],
  "next_page": "/api/search?query=machine+learning&page=2"
}
```

---

## Versioning

API version is included in all responses:
```json
{
  "server_version": "0.2.0"
}
```

Breaking changes will increment major version (1.0.0).

---

## Support & Troubleshooting

### Common Issues

**Issue: 401 Unauthorized**
- Solution: Check JWT token, regenerate if expired

**Issue: 429 Rate Limit**
- Solution: Wait 60 seconds, reduce request frequency

**Issue: 404 Concept Not Found**
- Solution: Use `search_concepts` first to find correct concept_id

**Issue: 503 Service Unavailable**
- Solution: Server still initializing, wait 10 seconds

### Debug Mode

Enable debug logging in `.env`:
```bash
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f logs/ontology_mcp.log
```

### Audit Trail

All API calls logged to audit log:
```bash
tail -f logs/audit.log
```
