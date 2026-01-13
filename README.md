# Okta Sample Employee MCP Server

A standalone, production-ready MCP (Model Context Protocol) server for employee data access, secured with Okta token validation.

**Features:**
- ✅ Okta token validation on every request
- ✅ Scope-based permissions (mcp:read, mcp:write)
- ✅ 6 employee management tools
- ✅ Three transport options (REST API, MCP HTTP, stdio)
- ✅ Production-ready with Docker & Render deployment
- ✅ MCP specification compliant

## Quick Start

### Prerequisites
- Python 3.9+
- Okta tenant with authorization server
- Valid Okta token with `mcp:read` or `mcp:write` scope

### Setup

```bash
# Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp env.template .env
# Edit .env with:
#   OKTA_DOMAIN=your-domain.okta.com
#   OKTA_AUTHORIZATION_SERVER_ID=your-auth-server-id

# Run
./start_server.sh
# Server runs on http://localhost:8001
```

## Available Tools

All tools require `mcp:read` or `mcp:write` scope:

| Tool | Description | Arguments |
|------|-------------|-----------|
| `list_employees` | List active employees | `status_filter` (Active/Inactive/All) |
| `get_employee_info` | Get employee details | `employee_identifier` (name or ID) |
| `get_department_info` | Get department info | `department_name` (optional) |
| `get_benefits_info` | Get benefits info | none |
| `get_salary_info` | Get salary bands | none |
| `get_onboarding_info` | Get onboarding process | none |

## Usage Examples

### 1. REST API

**List Tools:**
```bash
curl -X GET http://localhost:8001/tools \
  -H "Authorization: Bearer $TOKEN"
```

**Call Tool:**
```bash
curl -X POST http://localhost:8001/call_tool \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "list_employees",
    "arguments": {"status_filter": "Active"}
  }'
```

**Response:**
```json
{
  "result": {
    "employees": [
      {
        "employee_id": "EMP001",
        "name": "Jane Doe",
        "department": "Engineering",
        "title": "Senior Engineer",
        "manager": "John Smith",
        "status": "Active"
      }
    ],
    "total_count": 15,
    "status_filter": "Active"
  },
  "token_info": {
    "sub": "user@example.com",
    "scope": "mcp:read",
    "exp": 1704067200
  }
}
```

### 2. MCP Streamable HTTP (JSON-RPC)

**Initialize Connection:**
```bash
# Use -i to see response headers
curl -i -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {},
    "id": "1"
  }'
```

**Response Headers** (save the Mcp-Session-Id):
```
HTTP/1.1 200 OK
mcp-session-id: 550e8400-e29b-41d4-a716-446655440000
content-type: application/json
...
```

**Extract Session ID (Recommended):**
```bash
# Extract and save session ID
SESSION_ID=$(curl -s -i -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":"1"}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

echo "Session ID: $SESSION_ID"
```

**List Tools:**
```bash
# Use the SESSION_ID from above
curl -X POST http://localhost:8001/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": "2"
  }'
```

**Call Tool:**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "tool_name": "list_employees",
      "arguments": {"status_filter": "Active"}
    },
    "id": "3"
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "employees": [
      {
        "employee_id": "EMP001",
        "name": "Jane Doe",
        "department": "Engineering",
        "title": "Senior Engineer",
        "manager": "John Smith",
        "status": "Active"
      }
    ],
    "total_count": 15,
    "status_filter": "Active"
  },
  "id": "3"
}
```

**Terminate Session:**
```bash
curl -X DELETE http://localhost:8001/mcp \
  -H "Mcp-Session-Id: $SESSION_ID"
```

### 3. stdio Transport (Subprocess)

**Start Server:**
```bash
python -m mcp_server.stdio_transport
```

**Python Integration:**
```python
import subprocess
import json

# Start server
proc = subprocess.Popen(
    ["python", "-m", "mcp_server.stdio_transport"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

def send_request(method, params=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": "1"
    }
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())

# Initialize
response = send_request("initialize", {})
print(response)

# List tools
response = send_request("tools/list")
print(response)

# Call tool
response = send_request("tools/call", {
    "tool_name": "list_employees",
    "arguments": {"status_filter": "Active"}
})
print(response)
```

## Configuration

**`.env` Template:**

```env
# REQUIRED: Your Okta domain
OKTA_DOMAIN=dev-12345.okta.com

# REQUIRED: Authorization Server ID
OKTA_AUTHORIZATION_SERVER_ID=employee-mcp-server

# OPTIONAL: Expected audience for token validation
# Leave empty to skip audience validation
OKTA_AUDIENCE=

# OPTIONAL: Server settings
PORT=8001
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**How It Works:**

The server auto-discovers OAuth 2.0 configuration from:
```
https://{OKTA_DOMAIN}/oauth2/{OKTA_AUTHORIZATION_SERVER_ID}/.well-known/oauth-authorization-server
```

This provides:
- JWKS URL (for token signature validation)
- Issuer (for audience validation)
- All OAuth 2.0 endpoints

## Token Requirements

Your Okta token must have:
- **Valid signature** (verified against JWKS)
- **Not expired** (checked against exp claim)
- **Correct scope** (mcp:read or mcp:write in scp or scope claim)
- **Matching audience** (if OKTA_AUDIENCE is set)

**Token Example:**
```json
{
  "scp": ["mcp:read"],
  "sub": "user@example.com",
  "aud": "https://mcp.streamward.com",
  "exp": 1704067200,
  "iss": "https://dev-12345.okta.com/oauth2/auss2..."
}
```

## Testing

### Health Check
```bash
curl http://localhost:8001/health
```

### REST API
```bash
export TOKEN="your_okta_token"

curl -X POST http://localhost:8001/call_tool \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "list_employees", "arguments": {}}'
```

### MCP HTTP
```bash
# Initialize (no auth)
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": "1"}'

# Get SESSION_ID from response header and use in next requests
```

### stdio
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":"1"}' | \
python -m mcp_server.stdio_transport
```

## Troubleshooting

**"Invalid token for MCP request"**
- Token expired or invalid signature
- Check token with `jwt.io` (don't submit secrets there)

**"Permission denied"**
- Token doesn't have `mcp:read` or `mcp:write` scope
- Check token `scp` claim (Okta) or `scope` claim (OAuth)

**"Discovery failed"**
- Check OKTA_DOMAIN and OKTA_AUTHORIZATION_SERVER_ID
- Verify values match your Okta setup

**Server won't start**
- Ensure dependencies installed: `pip install -r requirements.txt`
- Check port 8001 isn't already in use: `lsof -i :8001`

## Deployment

### Docker
```bash
docker build -t okta-mcp .
docker run -p 8001:8001 \
  -e OKTA_DOMAIN=your-domain \
  -e OKTA_AUTHORIZATION_SERVER_ID=your-auth-server \
  okta-mcp
```

### Render
See `deployment/render.yaml` for one-click deployment

### Manual
```bash
python -m uvicorn mcp_server.main:app --host 0.0.0.0 --port 8001
```

## API Docs

Interactive API documentation available at: `http://localhost:8001/docs`

## Transport Comparison

| Feature | REST API | MCP HTTP | stdio |
|---------|----------|----------|-------|
| Standards Compliant | ❌ | ✅ | ✅ |
| Token Validation | ✅ | ✅ | ⚠️ |
| Session Management | ❌ | ✅ | ❌ |
| Network Ready | ✅ | ✅ | ❌ |
| IDE Integration | ❌ | ✅ | ✅ |
| Claude Desktop | ❌ | ✅ | ✅ |

Choose based on your use case:
- **REST API** - Custom integrations, testing
- **MCP HTTP** - Standard MCP clients, production
- **stdio** - Claude Desktop, IDE integration

## MCP Compatibility

This server is fully compatible with standard MCP clients:
- ✅ langchain-mcp-adapters
- ✅ Claude Desktop
- ✅ Cline / Cursor integration
- ✅ continue.dev
- ✅ All spec-compliant MCP clients

Tool definitions follow MCP specification with proper `inputSchema` field for parameter validation.

## License

See LICENSE file

## Support

For issues or questions, refer to:
- [MCP Specification](https://modelcontextprotocol.io/)
- [Okta OAuth 2.0](https://developer.okta.com/docs/concepts/oauth-openid/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
