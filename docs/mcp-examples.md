# MCP Integration Examples

This document provides practical examples of using aider with MCP (Model Context Protocol) integration.

## Basic Examples

### Example 1: Code Analysis Workflow

**Setup:**
```bash
aider --enable-aider-mcp-server
```

**Chat Session:**
```
User: Analyze all Python files in my project and identify potential issues.

Aider: I'll analyze your Python files using the MCP file analysis tool.

[Aider uses the analyze_file MCP tool on each .py file]

Analysis Results:
📄 src/main.py (127 lines, Python)
   - Complexity: 4.2/10
   - Issues: 2 TODO comments, 1 FIXME
   
📄 src/utils.py (89 lines, Python) 
   - Complexity: 2.1/10
   - Issues: None found
   
📄 src/complex_algorithm.py (245 lines, Python)
   - Complexity: 8.7/10 ⚠️
   - Issues: File is large (>200 lines), 3 TODO comments

The most complex file is src/complex_algorithm.py. Would you like me to suggest refactoring to reduce complexity?

User: Yes, please suggest improvements for the complex file.

Aider: [Analyzes the complex file and suggests specific refactoring improvements]
```

### Example 2: Test-Driven Development

**Setup:**
```bash
aider --enable-aider-mcp-server --auto-test
```

**Chat Session:**
```
User: Run my tests and fix any failures.

Aider: I'll run your tests using the MCP command execution tool.

[Uses run_command MCP tool to execute tests]

Test Results:
✅ 15 tests passed
❌ 3 tests failed

Failed Tests:
1. test_user_authentication.py::test_invalid_login
   - AssertionError: Expected 401, got 500
   - Duration: 0.12s

2. test_data_processing.py::test_large_dataset
   - TimeoutError: Operation timed out after 30s
   - Duration: 30.0s

3. test_api_endpoints.py::test_user_creation
   - KeyError: 'email' not found in response
   - Duration: 0.08s

Let me analyze the failing test files and related source code to identify the issues.

[Uses analyze_file and search_codebase MCP tools to investigate]

I found the issues:
1. Authentication endpoint returning 500 instead of 401 (src/auth.py:45)
2. Data processing timeout needs optimization (src/processor.py:123)
3. API response missing email field (src/api.py:67)

Would you like me to implement the fixes?
```

### Example 3: Project Exploration

**Setup:**
```bash
aider --enable-aider-mcp-server
```

**Chat Session:**
```
User: I'm new to this codebase. Can you help me understand the project structure and find the main entry points?

Aider: I'll help you explore the codebase using MCP tools.

[Uses get_repo_structure MCP tool]

Project Structure:
📁 src/
  📄 main.py (127 lines) - Main application entry point
  📄 config.py (45 lines) - Configuration management
  📄 models.py (203 lines) - Data models
  📁 api/
    📄 routes.py (156 lines) - API route definitions
    📄 middleware.py (78 lines) - Request middleware
  📁 services/
    📄 auth_service.py (134 lines) - Authentication logic
    📄 data_service.py (189 lines) - Data processing
📁 tests/
  📄 test_main.py (89 lines)
  📄 test_api.py (145 lines)
📁 docs/
  📄 README.md
  📄 API.md

[Uses search_codebase MCP tool to find entry points]

Main Entry Points Found:
1. src/main.py:15 - `def main()` - Application startup
2. src/api/routes.py:23 - `app = FastAPI()` - API server
3. src/services/auth_service.py:34 - `class AuthService` - Authentication

The application appears to be a FastAPI-based web service with authentication. The main entry point is in src/main.py. Would you like me to analyze any specific component?

User: Show me the main function and explain what it does.

Aider: [Uses file:// MCP resource to read src/main.py and explains the main function]
```

## Advanced Examples

### Example 4: External Tool Integration

**Setup:**
```bash
# Connect to filesystem and web search servers
aider --enable-aider-mcp-server \
      --mcp-servers "filesystem:stdio:mcp-server-filesystem ." \
      --mcp-servers "search:stdio:mcp-server-brave-search"
```

**Configuration file (`.aider.mcp.json`):**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 45,
    "context_limit": 15000
  },
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "."],
      "enabled": true
    },
    {
      "name": "web-search",
      "transport": "stdio", 
      "command": ["mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key-here"
      },
      "enabled": true
    },
    {
      "name": "aider-tools",
      "transport": "websocket",
      "url": "ws://localhost:8000/mcp",
      "enabled": true
    }
  ]
}
```

**Chat Session:**
```
User: I need to implement OAuth authentication. Can you research best practices and help me implement it?

Aider: I'll research OAuth best practices and help you implement authentication.

[Uses web-search MCP server to find current OAuth best practices]

Research Results:
- OAuth 2.1 is the current standard (2023)
- PKCE (Proof Key for Code Exchange) is now required
- JWT tokens should use RS256 signing
- Refresh tokens should rotate for security

[Uses filesystem MCP server to examine current auth implementation]

Current Implementation Analysis:
- You have basic session-based auth in src/auth.py
- No OAuth implementation found
- Database models support user accounts

[Uses aider-tools MCP server to analyze complexity]

Implementation Plan:
1. Add OAuth 2.1 dependencies (authlib, python-jose)
2. Create OAuth provider configuration
3. Implement PKCE flow endpoints
4. Add JWT token handling with RS256
5. Update user models for OAuth data
6. Add refresh token rotation

Would you like me to start implementing this step by step?
```

### Example 5: Database Integration

**Setup with custom MCP server:**

**Custom Database MCP Server (`db_server.py`):**
```python
from fastmcp import FastMCP
import asyncpg
import json

mcp = FastMCP("database-tools")

@mcp.tool()
async def query_database(sql: str) -> dict:
    """Execute SQL query and return results"""
    conn = await asyncpg.connect("postgresql://user:pass@localhost/db")
    try:
        results = await conn.fetch(sql)
        return {
            "rows": [dict(row) for row in results],
            "count": len(results)
        }
    finally:
        await conn.close()

@mcp.tool()
async def get_table_schema(table_name: str) -> dict:
    """Get table schema information"""
    conn = await asyncpg.connect("postgresql://user:pass@localhost/db")
    try:
        schema = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = $1
        """, table_name)
        return {
            "table": table_name,
            "columns": [dict(col) for col in schema]
        }
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="localhost", port=9000)
```

**Start the custom server:**
```bash
python db_server.py
```

**Connect aider:**
```bash
aider --enable-aider-mcp-server \
      --mcp-servers "database:websocket:ws://localhost:9000/mcp"
```

**Chat Session:**
```
User: Help me understand my database schema and optimize a slow query.

Aider: I'll examine your database schema and help optimize queries.

[Uses database MCP server to get table schemas]

Database Schema Analysis:
📊 users table:
  - id (integer, not null)
  - email (varchar, not null) 
  - created_at (timestamp, not null)
  - last_login (timestamp, nullable)

📊 orders table:
  - id (integer, not null)
  - user_id (integer, not null)
  - total (decimal, not null)
  - status (varchar, not null)
  - created_at (timestamp, not null)

[Uses query_database MCP tool to analyze query performance]

Current Query Performance:
```sql
SELECT u.email, COUNT(o.id) as order_count 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
GROUP BY u.email
```
- Execution time: 2.3 seconds
- Rows examined: 1,250,000

Optimization Recommendations:
1. Add index on orders.user_id (missing foreign key index)
2. Add composite index on (user_id, created_at) for time-based queries
3. Consider partitioning orders table by date

Would you like me to generate the index creation SQL?

User: Yes, create the optimized indexes.

Aider: [Generates optimized index creation SQL and explains the performance benefits]
```

### Example 6: Multi-Language Project

**Setup:**
```bash
aider --enable-aider-mcp-server
```

**Chat Session:**
```
User: This is a full-stack project with Python backend and React frontend. Can you analyze both parts and suggest improvements?

Aider: I'll analyze both the Python backend and React frontend components.

[Uses get_repo_structure MCP tool to understand project layout]

Project Structure Analysis:
📁 backend/ (Python)
  📁 src/
    📄 main.py (FastAPI application)
    📄 models.py (SQLAlchemy models)
    📄 routes.py (API endpoints)
  📄 requirements.txt
  📄 Dockerfile

📁 frontend/ (React/TypeScript)
  📁 src/
    📁 components/
    📁 pages/
    📁 hooks/
    📄 App.tsx
  📄 package.json
  📄 tsconfig.json

[Uses analyze_file MCP tool on key files from both parts]

Backend Analysis (Python):
📄 backend/src/main.py (156 lines, Python)
   - Complexity: 3.4/10
   - Issues: Missing error handling middleware
   
📄 backend/src/models.py (234 lines, Python)
   - Complexity: 5.7/10
   - Issues: Some models lack validation

📄 backend/src/routes.py (189 lines, Python)
   - Complexity: 6.2/10
   - Issues: 4 TODO comments, missing input validation

Frontend Analysis (TypeScript):
📄 frontend/src/App.tsx (89 lines, TypeScript)
   - Complexity: 2.8/10
   - Issues: None found

📄 frontend/src/components/UserList.tsx (145 lines, TypeScript)
   - Complexity: 4.1/10
   - Issues: Missing error boundaries

[Uses search_codebase MCP tool to find patterns]

Cross-cutting Concerns Found:
- API endpoints: 12 routes in backend
- API calls: 8 fetch calls in frontend
- Error handling: Inconsistent patterns
- Authentication: JWT tokens used

Recommendations:
1. Backend: Add global error handling middleware
2. Backend: Implement input validation with Pydantic
3. Frontend: Add React error boundaries
4. Frontend: Implement consistent error handling
5. Both: Add comprehensive logging
6. Both: Improve test coverage

Would you like me to implement any of these improvements?
```

## Configuration Examples

### Example 7: Team Configuration

**Global team config (`~/.aider/mcp-config.json`):**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 60,
    "max_retries": 5,
    "context_limit": 20000,
    "cache_ttl": 600,
    "log_level": "INFO"
  },
  "servers": [
    {
      "name": "company-tools",
      "transport": "websocket",
      "url": "wss://mcp.company.com/tools",
      "enabled": true
    },
    {
      "name": "shared-filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "/shared/projects"],
      "enabled": true
    }
  ]
}
```

**Project-specific config (`.aider.mcp.json`):**
```json
{
  "settings": {
    "context_limit": 15000
  },
  "servers": [
    {
      "name": "project-database",
      "transport": "websocket",
      "url": "ws://localhost:5432/mcp",
      "enabled": true
    },
    {
      "name": "aider-tools",
      "transport": "websocket",
      "url": "ws://localhost:8000/mcp", 
      "enabled": true
    }
  ]
}
```

### Example 8: Development vs Production

**Development (`.aider.mcp.json`):**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 30,
    "log_level": "DEBUG"
  },
  "servers": [
    {
      "name": "local-filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "."],
      "enabled": true
    },
    {
      "name": "dev-database",
      "transport": "websocket",
      "url": "ws://localhost:5432/mcp",
      "enabled": true
    },
    {
      "name": "aider-tools",
      "transport": "websocket",
      "url": "ws://localhost:8000/mcp",
      "enabled": true
    }
  ]
}
```

**Production environment variables:**
```bash
export AIDER_MCP_CONFIG="/etc/aider/prod-mcp-config.json"
export AIDER_MCP_SERVER_PORT="8080"
```

**Production config (`/etc/aider/prod-mcp-config.json`):**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 60,
    "max_retries": 3,
    "context_limit": 10000,
    "log_level": "WARNING"
  },
  "servers": [
    {
      "name": "prod-filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "/app/src"],
      "enabled": true
    },
    {
      "name": "prod-database",
      "transport": "websocket",
      "url": "wss://db.company.com:5432/mcp",
      "enabled": true
    }
  ]
}
```

## Performance Examples

### Example 9: Large Codebase Optimization

**Configuration for large projects:**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 120,
    "max_retries": 2,
    "context_limit": 5000,
    "cache_ttl": 1800,
    "log_level": "WARNING"
  },
  "servers": [
    {
      "name": "aider-tools",
      "transport": "websocket",
      "url": "ws://localhost:8000/mcp",
      "enabled": true
    }
  ]
}
```

**Usage pattern:**
```bash
aider --enable-aider-mcp-server
```

**Chat Session:**
```
User: This is a large codebase with 500+ files. Help me find and fix performance issues.

Aider: I'll analyze your large codebase efficiently using targeted MCP tools.

[Uses search_codebase MCP tool with specific patterns]

Performance Issue Search:
🔍 Searching for common performance anti-patterns...

Found Issues:
1. N+1 Query Pattern (12 occurrences)
   - src/services/user_service.py:45
   - src/api/orders.py:123
   - src/models/product.py:67

2. Large Loop Operations (8 occurrences)
   - src/data/processor.py:234 (10,000+ iterations)
   - src/utils/converter.py:89 (nested loops)

3. Memory Leaks (3 potential)
   - src/cache/manager.py:156 (unclosed connections)
   - src/workers/background.py:78 (growing lists)

[Uses analyze_file MCP tool on specific problematic files]

Priority Fixes:
1. HIGH: Fix N+1 queries in user_service.py (affects 80% of API calls)
2. MEDIUM: Optimize data processor loops (affects batch jobs)
3. LOW: Fix memory leaks (affects long-running processes)

Would you like me to start with the high-priority N+1 query fixes?
```

### Example 10: Real-time Development

**Setup for fast iteration:**
```bash
aider --enable-aider-mcp-server --watch-files
```

**Configuration for speed:**
```json
{
  "settings": {
    "enabled": true,
    "timeout": 15,
    "max_retries": 1,
    "context_limit": 8000,
    "cache_ttl": 60,
    "log_level": "ERROR"
  }
}
```

**Chat Session:**
```
User: I'm making rapid changes. Help me test each change quickly.

Aider: I'll help you test changes rapidly using MCP tools.

[File watcher detects changes to src/api.py]

Change Detected: src/api.py modified

[Uses run_command MCP tool to run quick tests]

Quick Test Results:
✅ Unit tests: 23/23 passed (1.2s)
✅ Linting: No issues found (0.3s)
⚠️  Type check: 1 warning in src/api.py:45

[Uses analyze_file MCP tool on changed file]

Change Analysis:
- Added new endpoint: POST /api/users
- Complexity increased: 4.1 → 4.3 (acceptable)
- Type warning: Missing return type annotation

Quick Fix Applied:
- Added return type annotation: -> Dict[str, Any]

All checks now pass! Ready for next change.
```

These examples demonstrate the power and flexibility of MCP integration with aider, showing how it can enhance development workflows across different scenarios and project types.