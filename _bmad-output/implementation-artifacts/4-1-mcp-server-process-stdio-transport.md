# Story 4.1: MCP Server Process & stdio Transport

Status: ready-for-dev

## Story

As an AI agent developer,
I want a standalone MCP server process that connects Resili to my agent client,
so that I can add Resili scraping capability with a single config entry and no wrapper code.

## Acceptance Criteria

1. **Given** `python backend/mcp_server.py` is run with `RESILI_API_KEY` set in environment, **When** started, **Then** the process accepts MCP stdio protocol messages without error.

2. **Given** `mcp_server.py`, **When** reviewed, **Then** it directly imports `app.scraping.fetcher` and `app.scraping.dynamic` — it makes **no** HTTP calls to the FastAPI server.

3. **Given** Claude Desktop `mcp_config.json` with Resili entry, **When** added and Claude Desktop is restarted, **Then** Resili tools appear in the tool list.

4. **Given** the MCP server process crashes, **When** it crashes, **Then** the FastAPI API server continues running independently.

5. **Given** `mcp_server.py`, **When** reviewed, **Then** it declares a top-level constant `MCP_SPEC_VERSION` with the MCP protocol version it implements.

## Tasks / Subtasks

- [ ] Research current MCP Python SDK (AC: 1, 3, 5)
  - [ ] Check `mcp` package on PyPI — latest stable version
  - [ ] Understand stdio transport API

- [ ] Create `backend/mcp_server.py` (AC: 1, 2, 4, 5)
  - [ ] Standalone script — NOT part of FastAPI app
  - [ ] Direct import `app.scraping.fetcher`, `app.scraping.dynamic`
  - [ ] `MCP_SPEC_VERSION` constant
  - [ ] stdio transport handler

- [ ] Add `mcp` to requirements (AC: 1)
  - [ ] `backend/requirements.txt`: add `mcp>=1.0`

- [ ] Viết tests (AC: 1, 2)

## Dev Notes

### MCP Python SDK — Current State (2026)

```bash
pip install mcp
```

Latest stable: `mcp>=1.0` (Anthropic's official Python SDK for MCP). The SDK provides:
- `mcp.server.Server` class
- `mcp.server.stdio.stdio_server()` context manager
- Tool definitions via `@server.list_tools()` and `@server.call_tool()`

### `backend/mcp_server.py` — Standalone Process (Dec-E)

```python
#!/usr/bin/env python3
"""
Resili MCP Server — Standalone stdio process.
Direct import of scraping modules — NO HTTP calls to FastAPI (Dec-E).
Run with: python mcp_server.py (with RESILI_API_KEY in environment)
"""
import asyncio
import sys
import os

# CRITICAL: Add backend/ to Python path for app.* imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ErrorCode, McpError

# MCP protocol version this server implements (AC: 5)
MCP_SPEC_VERSION = "2024-11-05"  # Update to current MCP spec version

# Initialize MCP server
server = Server("resili")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Declare available tools to the MCP client."""
    return [
        Tool(
            name="fetch_page",
            description=(
                "Fetch and convert a web page to Markdown or JSON. "
                "Use for static pages, documentation, news articles — no JavaScript rendering required. "
                "Fast (1-3s). Costs 1 credit."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"},
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                        "description": "Output format"
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="fetch_dynamic_page",
            description=(
                "Fetch and render a JavaScript-heavy web page using a full browser. "
                "Use for SPAs, dashboards, pages that require browser rendering. "
                "Slower (5-15s). Costs 5 credits. Requires Pro tier."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"},
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "json"],
                        "default": "markdown",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls — directly import scraping modules (Dec-E)."""
    from app.core.ssrf_guard import validate_url
    from app.core.errors import SSRFBlockedError

    url = arguments.get("url", "")
    fmt = arguments.get("format", "markdown")

    # SSRF validation even in MCP context
    try:
        validate_url(url)
    except SSRFBlockedError as e:
        raise McpError(ErrorCode.InvalidParams, f"SSRF_BLOCKED: {e.message}")

    if name == "fetch_page":
        from app.scraping.fetcher import fetch_url
        from app.scraping.formatter import html_to_markdown, html_to_json
        try:
            html = await fetch_url(url)
            content = html_to_markdown(html) if fmt == "markdown" else html_to_json(html)
            return [TextContent(type="text", text=content)]
        except Exception as e:
            raise McpError(ErrorCode.InternalError, str(e))

    elif name == "fetch_dynamic_page":
        from app.scraping.dynamic import fetch_dynamic_url
        from app.scraping.formatter import html_to_markdown, html_to_json
        try:
            html = await fetch_dynamic_url(url)
            content = html_to_markdown(html) if fmt == "markdown" else html_to_json(html)
            return [TextContent(type="text", text=content)]
        except Exception as e:
            raise McpError(ErrorCode.InternalError, str(e))

    raise McpError(ErrorCode.MethodNotFound, f"Unknown tool: {name}")


async def main():
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1])


if __name__ == "__main__":
    asyncio.run(main())
```

### Process Isolation (Dec-E)

`mcp_server.py` adalah STANDALONE SCRIPT — bukan module of FastAPI. Khi chạy:
```bash
python backend/mcp_server.py
```

Process này:
- Không share memory với FastAPI process
- Không make HTTP calls đến FastAPI
- Import trực tiếp `app.scraping.*` module
- Crash → chỉ MCP process chết, FastAPI vẫn chạy (AC: 4)

**Verify:** Sau khi `kill <mcp_pid>`, `curl http://localhost:8000/health` vẫn trả 200.

### MCP_SPEC_VERSION (AC: 5)

```python
# Top of mcp_server.py
MCP_SPEC_VERSION = "2024-11-05"  # Or latest MCP spec version at time of implementation
```

Check current MCP spec version at: https://spec.modelcontextprotocol.io/

### Claude Desktop Config (AC: 3)

```json
{
  "mcpServers": {
    "resili": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_server.py"],
      "env": {
        "RESILI_API_KEY": "rsl_your_key_here"
      }
    }
  }
}
```

File location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

### requirements.txt

```
mcp>=1.0
```

Note: `mcp` package requires Python 3.10+. Resili uses Python 3.13 → compatible.

### References

- [Source: architecture.md#Dec-E-MCP-Server-Process-Model] — standalone process, direct import
- [Source: epics.md#Story-4.1] — acceptance criteria
- [Source: architecture.md#MCP-Flow] — data flow diagram

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/requirements.txt` — add mcp>=1.0

**NEW:**
- `backend/mcp_server.py`
- `backend/tests/test_mcp_server.py`
