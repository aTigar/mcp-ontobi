# Deployment Guide - Obsidian Ontology MCP Server

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Security Hardening](#security-hardening)
6. [Monitoring](#monitoring)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 22.04+), macOS, or Windows 10/11
- **Python**: 3.11 or higher
- **RAM**: 2GB minimum, 4GB recommended for vaults >5,000 concepts
- **Disk**: 1GB for application + vault size
- **Network**: Localhost access (127.0.0.1)

### Software Dependencies

- Python 3.11+ with pip
- Git (for version control)
- Optional: uv (faster package installer)
- Optional: nginx (for production with TLS)

### Access Requirements

- Read access to Obsidian vault directory
- Write access to log directory
- Port 8000 available (or configure alternative)

---

## Local Development Setup

### Step 1: Clone or Create Project

```bash
# Create project directory
mkdir obsidian-ontology-mcp
cd obsidian-ontology-mcp

# Initialize git
git init
```

### Step 2: Create Virtual Environment

**Option A: Using uv (recommended - faster)**
```bash
# Install uv if not available
pip install uv

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Option B: Using standard venv**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Or with standard pip
pip install -e ".[dev]"
```

### Step 4: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env  # or vim, code, etc.
```

**Minimum required configuration:**
```bash
# .env
VAULT_PATH=/absolute/path/to/your/obsidian/vault
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt hash - see below>
```

**Generate password hash:**
```bash
python -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('your_secure_password_here'))
"
```

Copy the output hash to `ADMIN_PASSWORD_HASH` in `.env`.

### Step 5: Verify Installation

```bash
# Test extraction
python -c "
from pathlib import Path
from src.obsidian_ontology_mcp.extraction.skos_extractor import SKOSExtractor
from src.obsidian_ontology_mcp.config import settings

extractor = SKOSExtractor(settings.vault_path)
concepts = extractor.extract_all_concepts()
print(f'✓ Found {len(concepts)} concepts in vault')
"
```

Expected output:
```
✓ Found 127 concepts in vault
```

### Step 6: Run Server

**Option A: MCP Server (for OpenCode)**
```bash
python scripts/run_mcp_server.py
```

Server will listen on STDIO for MCP protocol.

**Option B: HTTP Server (for n8n)**
```bash
python scripts/run_http_server.py
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Option C: Dual Mode (both MCP and HTTP)**
```bash
python scripts/run_dual_server.py
```

### Step 7: Test HTTP Server

```bash
# Health check
curl http://127.0.0.1:8000/health

# Get JWT token
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_secure_password_here"}'

# Expected: {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 1800}

# Test authenticated endpoint (replace TOKEN)
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'
```

---

## Production Deployment

### Deployment Options

1. **Local Server** (Leipzig machine, localhost only)
2. **Remote Server** (VPS with nginx reverse proxy)
3. **Docker Container** (portable, isolated)

### Option 1: Local Server (Recommended for Academic Use)

This is the simplest and most secure option for personal/academic use.

**Setup:**
1. Follow "Local Development Setup" above
2. Configure systemd service for auto-start (Linux)

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/obsidian-ontology-mcp.service
```

**Service file:**
```ini
[Unit]
Description=Obsidian Ontology MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/obsidian-ontology-mcp
Environment="PATH=/home/your-username/obsidian-ontology-mcp/.venv/bin"
ExecStart=/home/your-username/obsidian-ontology-mcp/.venv/bin/python scripts/run_http_server.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable obsidian-ontology-mcp
sudo systemctl start obsidian-ontology-mcp
sudo systemctl status obsidian-ontology-mcp
```

**View logs:**
```bash
sudo journalctl -u obsidian-ontology-mcp -f
```

### Option 2: Remote Server with TLS

For remote access (e.g., from other machines), add nginx reverse proxy with TLS.

**Prerequisites:**
- Domain name pointing to server IP
- Ports 80 and 443 open in firewall

**Install nginx and certbot:**
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

**Create nginx configuration:**
```bash
sudo nano /etc/nginx/sites-available/ontology-mcp
```

**Nginx configuration:**
```nginx
# /etc/nginx/sites-available/ontology-mcp

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (will be created by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to FastAPI backend
    location / {
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint (bypass rate limit)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/ontology-mcp /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**Obtain SSL certificate:**
```bash
sudo certbot --nginx -d your-domain.com
```

Follow prompts to configure automatic renewal.

**Configure firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

**Update .env for remote access:**
```bash
# Allow connections from nginx
HTTP_HOST=127.0.0.1  # Keep localhost (nginx proxies)

# Update CORS if needed
HTTP_ENABLE_CORS=true
HTTP_ALLOWED_ORIGINS=["https://your-n8n-instance.com"]
```

### Option 3: Docker Deployment (Advanced)

**Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create log directory
RUN mkdir -p /app/logs

# Expose HTTP port
EXPOSE 8000

# Run HTTP server
CMD ["python", "scripts/run_http_server.py"]
```

**Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  ontology-mcp:
    build: .
    container_name: obsidian-ontology-mcp
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - /path/to/obsidian/vault:/vault:ro  # Read-only vault
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
    environment:
      - VAULT_PATH=/vault
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Build and run:**
```bash
docker-compose up -d
docker-compose logs -f
```

---

## Configuration

### Environment Variables Reference

**Core Settings:**
```bash
# Vault
VAULT_PATH=/path/to/vault        # Required
VAULT_WATCH_ENABLED=true         # Auto-update on file changes

# Server
MCP_SERVER_NAME="Obsidian Ontology Server"
MCP_SERVER_VERSION="0.2.0"
HTTP_HOST=127.0.0.1              # Localhost only (secure)
HTTP_PORT=8000

# Authentication
ENABLE_AUTHENTICATION=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt hash>

# JWT
JWT_SECRET_KEY=<auto-generated or set>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Security Limits
MAX_QUERY_LENGTH=1000
MAX_CONTEXT_DEPTH=3
MAX_RESULTS_PER_QUERY=100
MAX_CONCEPT_CONTENT_LENGTH=50000

# CORS (disable for localhost-only)
HTTP_ENABLE_CORS=false
HTTP_ALLOWED_ORIGINS=["http://localhost:5678"]

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/ontology_mcp.log
AUDIT_LOG_FILE=logs/audit.log

# Performance
GRAPH_CACHE_ENABLED=true
GRAPH_CACHE_TTL=3600
```

### Logging Configuration

**Log levels:**
- `DEBUG`: Detailed information for debugging
- `INFO`: General operational messages (default)
- `WARNING`: Warning messages (non-critical)
- `ERROR`: Error messages

**Log rotation (Linux):**
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/ontology-mcp
```

**Logrotate configuration:**
```
/home/your-username/obsidian-ontology-mcp/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 your-username your-username
}
```

---

## Security Hardening

### Step 1: Generate Strong Secrets

```bash
# Generate JWT secret (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate strong admin password
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Update `.env` with generated values.

### Step 2: File Permissions

```bash
# Restrict .env file
chmod 600 .env

# Restrict log directory
chmod 700 logs/
```

### Step 3: Firewall Configuration

**UFW (Ubuntu):**
```bash
# Default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (if remote)
sudo ufw allow 22/tcp

# Allow HTTPS (if nginx)
sudo ufw allow 443/tcp

# DO NOT allow 8000/tcp (keep internal)

sudo ufw enable
```

### Step 4: Fail2ban (Optional)

Protect against brute-force login attempts:

```bash
sudo apt install fail2ban

# Create jail for API
sudo nano /etc/fail2ban/jail.local
```

**Fail2ban configuration:**
```ini
[ontology-mcp-auth]
enabled = true
port = https,http
filter = ontology-mcp-auth
logpath = /home/your-username/obsidian-ontology-mcp/logs/audit.log
maxretry = 5
bantime = 3600
findtime = 600
```

**Create filter:**
```bash
sudo nano /etc/fail2ban/filter.d/ontology-mcp-auth.conf
```

```ini
[Definition]
failregex = .*"event_type": "authentication".*"success": false.*"ip_address": "<HOST>"
ignoreregex =
```

```bash
sudo systemctl restart fail2ban
```

### Step 5: Regular Updates

```bash
# Create update script
nano scripts/update.sh
```

**Update script:**
```bash
#!/bin/bash
set -e

echo "Updating Obsidian Ontology MCP Server..."

# Pull latest code (if using git)
git pull

# Update dependencies
source .venv/bin/activate
pip install --upgrade -e ".[dev]"

# Run security checks
safety check
bandit -r src/

# Restart service
sudo systemctl restart obsidian-ontology-mcp

echo "Update complete!"
```

```bash
chmod +x scripts/update.sh
```

### Step 6: Security Scanning

```bash
# Install security tools
pip install safety bandit

# Check for vulnerable dependencies
safety check

# Static security analysis
bandit -r src/ -f json -o security-report.json

# Review report
cat security-report.json | jq
```

---

## Monitoring

### Health Checks

**HTTP health endpoint:**
```bash
curl http://127.0.0.1:8000/health
```

**Systemd monitoring:**
```bash
# Check service status
systemctl status obsidian-ontology-mcp

# View logs
journalctl -u obsidian-ontology-mcp -f
```

**Uptime monitoring (example with UptimeRobot):**
- Monitor: `https://your-domain.com/health`
- Interval: 5 minutes
- Alert: Email when down

### Log Analysis

**View recent errors:**
```bash
grep ERROR logs/ontology_mcp.log | tail -20
```

**View authentication failures:**
```bash
grep '"success": false' logs/audit.log | jq
```

**Count API calls per user:**
```bash
grep tool_call logs/audit.log | jq -r '.username' | sort | uniq -c
```

**Monitor response times:**
```bash
grep execution_time_ms logs/audit.log | jq '.details.execution_time_ms' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'
```

### Performance Monitoring

**System resources:**
```bash
# Install htop
sudo apt install htop

# Monitor process
htop -p $(pgrep -f "run_http_server.py")
```

**Memory usage:**
```bash
ps aux | grep "run_http_server.py" | awk '{print $6/1024 " MB"}'
```

---

## Backup & Recovery

### Backup Strategy

**What to backup:**
1. Obsidian vault (managed by Obsidian/git)
2. Configuration files (.env)
3. Logs (audit trail)

**Backup script:**
```bash
#!/bin/bash
BACKUP_DIR="/backup/ontology-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/env_$DATE.backup"

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

# Keep last 30 days
find "$BACKUP_DIR" -mtime +30 -delete

echo "Backup complete: $BACKUP_DIR"
```

**Automate with cron:**
```bash
crontab -e
```

Add:
```
0 2 * * * /home/your-username/obsidian-ontology-mcp/scripts/backup.sh
```

### Recovery

**Restore configuration:**
```bash
cp /backup/ontology-mcp/env_20260208_020000.backup .env
```

**Rebuild graph:**
```bash
# Graph is rebuilt automatically on startup from vault
sudo systemctl restart obsidian-ontology-mcp
```

---

## Troubleshooting

### Server Won't Start

**Check logs:**
```bash
tail -50 logs/ontology_mcp.log
```

**Common issues:**

1. **Vault path not found**
```
ValueError: Vault path does not exist: /path/to/vault
```
Solution: Verify `VAULT_PATH` in `.env` exists and is absolute path.

2. **Port already in use**
```
OSError: [Errno 98] Address already in use
```
Solution: Change `HTTP_PORT` in `.env` or kill process using port:
```bash
sudo lsof -ti:8000 | xargs kill -9
```

3. **Import errors**
```
ModuleNotFoundError: No module named 'fastmcp'
```
Solution: Reinstall dependencies:
```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### Authentication Failures

**Issue: 401 Unauthorized**

Check JWT token expiration:
```bash
# Decode token (first part before first dot is header)
echo "TOKEN_PAYLOAD_PART" | base64 -d | jq
```

Solution: Generate new token via `/api/auth/login`.

**Issue: Wrong password**

Regenerate password hash:
```bash
python -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'])
print(pwd_context.hash('new_password'))
"
```

Update `.env` with new hash and restart.

### Slow Performance

**Issue: Context expansion takes >5 seconds**

Solutions:
1. Reduce `max_depth` (use 1 or 2 instead of 3)
2. Switch to igraph for large vaults (>10k concepts)
3. Enable caching in `.env`:
```bash
GRAPH_CACHE_ENABLED=true
GRAPH_CACHE_TTL=3600
```

**Issue: High memory usage**

Monitor graph size:
```bash
curl http://127.0.0.1:8000/api/statistics
```

If >10,000 concepts, switch to igraph (see architecture.md).

### File Watcher Issues

**Issue: Changes not reflected**

Check watcher status in logs:
```bash
grep "Vault watcher" logs/ontology_mcp.log
```

Restart server to reinitialize watcher:
```bash
sudo systemctl restart obsidian-ontology-mcp
```

### Integration Issues

**OpenCode not seeing MCP server**

Verify MCP configuration path:
```bash
# Check OpenCode config file location
# Usually: ~/.config/opencode/mcp.json or similar
```

Ensure absolute paths in config:
```json
{
  "mcpServers": {
    "obsidian-ontology": {
      "command": "python",
      "args": ["/absolute/path/to/scripts/run_mcp_server.py"]
    }
  }
}
```

**n8n connection refused**

Check server is running:
```bash
curl http://127.0.0.1:8000/health
```

Verify n8n can reach server (same machine or network route).

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor logs for errors
- Check disk space: `df -h`

**Weekly:**
- Review audit log for security events
- Check for failed authentication attempts

**Monthly:**
- Update dependencies: `pip install --upgrade -e ".[dev]"`
- Run security scan: `safety check && bandit -r src/`
- Review and rotate logs

**Quarterly:**
- Update Python version if new stable release
- Review and update configuration
- Test disaster recovery procedure

---

## Getting Help

**Logs to include when reporting issues:**
```bash
# Last 100 lines of main log
tail -100 logs/ontology_mcp.log > debug_log.txt

# System information
python --version >> debug_log.txt
pip list >> debug_log.txt
uname -a >> debug_log.txt

# Graph statistics
curl http://127.0.0.1:8000/api/statistics >> debug_log.txt
```

**Sanitize sensitive information before sharing:**
- Remove JWT tokens
- Remove password hashes
- Remove absolute paths if sensitive
