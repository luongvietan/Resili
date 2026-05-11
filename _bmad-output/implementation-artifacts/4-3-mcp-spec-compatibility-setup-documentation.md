# Story 4.3: MCP Spec Compatibility & Setup Documentation

Status: ready-for-dev

## Story

As an AI agent developer,
I want clear MCP spec compatibility information and copy-paste setup instructions,
so that I can diagnose connection issues and integrate Resili into any MCP-compatible client.

## Acceptance Criteria

1. **Given** an MCP client using an incompatible protocol version, **When** it connects, **Then** the error response includes: the MCP spec version Resili supports (`MCP_SPEC_VERSION`), the version sent by the client, and a docs URL.

2. **Given** `docs/mcp-setup.md`, **When** reviewed, **Then** it contains: exact 1-line JSON config for Claude Desktop, Cursor, and OpenAI agent tools; `RESILI_API_KEY` setup; and the supported `MCP_SPEC_VERSION`.

3. **Given** any MCP tool error (auth failure, credits exhausted, SSRF blocked), **When** returned, **Then** the error follows a consistent schema compatible with MCP protocol error format.

## Tasks / Subtasks

- [ ] Implement MCP version compatibility check (AC: 1)
  - [ ] `mcp_server.py`: intercept incompatible version → return structured error with version info

- [ ] Create `docs/mcp-setup.md` (AC: 2)
  - [ ] Claude Desktop config (JSON)
  - [ ] Cursor config (JSON)
  - [ ] OpenAI agent tools config
  - [ ] RESILI_API_KEY setup instructions
  - [ ] Supported MCP_SPEC_VERSION

- [ ] Standardize MCP error schema (AC: 3)
  - [ ] Consistent error format for auth, credits, SSRF errors

## Tasks / Subtasks

- [ ] Implement version check handler in mcp_server.py (AC: 1)
- [ ] Write docs/mcp-setup.md (AC: 2)
- [ ] Verify all MCP errors follow consistent schema (AC: 3)

## Dev Notes

### MCP Version Compatibility (AC: 1)

MCP SDK handles version negotiation. Custom version error:

```python
# mcp_server.py — Add version mismatch handler

@server.on_error()  # Or check MCP SDK for proper hook
async def handle_protocol_error(error_type: str, client_version: str):
    if error_type == "version_mismatch":
        return {
            "error": {
                "code": "MCP_VERSION_INCOMPATIBLE",
                "message": f"Client MCP version '{client_version}' is not compatible",
                "resili_supported_version": MCP_SPEC_VERSION,
                "client_version": client_version,
                "docs_url": "https://docs.resili.io/mcp/compatibility",
            }
        }
```

Check MCP Python SDK docs for exact error hook API. The MCP SDK may handle version negotiation automatically — verify with current SDK version.

### `docs/mcp-setup.md`

```markdown
# Resili MCP Server Setup

Integrate Resili's web scraping capabilities into your AI agent with a single configuration entry.

## Supported MCP Spec Version

`2024-11-05` (MCP_SPEC_VERSION in mcp_server.py)

## Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

Restart Claude Desktop after saving. The `fetch_page` and `fetch_dynamic_page` tools will appear.

## Cursor

Add to Cursor's MCP configuration (Settings → MCP):

```json
{
  "resili": {
    "command": "python",
    "args": ["/absolute/path/to/backend/mcp_server.py"],
    "env": {
      "RESILI_API_KEY": "rsl_your_key_here"
    }
  }
}
```

## OpenAI Agent Tools

For OpenAI Agents SDK, use the MCP tool adapter:

```python
from openai_agents_mcp import MCPServerStdio

resili_server = MCPServerStdio(
    command="python",
    args=["/path/to/backend/mcp_server.py"],
    env={"RESILI_API_KEY": "rsl_your_key_here"},
)
```

## Getting Your API Key

1. Sign up at https://resili.io
2. Go to Dashboard → API Keys
3. Click "Create new key"
4. Copy the key (shown only once)

## Troubleshooting

- **Tools not appearing:** Restart the MCP client after config changes
- **Version incompatible:** Check `MCP_SPEC_VERSION` in `mcp_server.py`; update your MCP client
- **Auth errors:** Verify `RESILI_API_KEY` is set correctly (must start with `rsl_`)
- **Dynamic not available:** DynamicFetcher requires Pro tier — upgrade at https://resili.io/dashboard
```

### Consistent MCP Error Schema (AC: 3)

All MCP errors should follow:
```python
raise McpError(
    ErrorCode.InvalidParams,  # or InternalError
    "ERROR_CODE: Human-readable message. Hint: suggested action. Docs: https://docs.resili.io/errors/..."
)
```

Map Resili errors to MCP errors:
- Auth failure → `ErrorCode.InvalidParams` with `INVALID_API_KEY`
- Credits exhausted → `ErrorCode.InvalidParams` with `CREDITS_EXHAUSTED`
- SSRF blocked → `ErrorCode.InvalidParams` with `SSRF_BLOCKED`
- Scraping failure → `ErrorCode.InternalError` with `SCRAPING_FAILED`

### References

- [Source: epics.md#Story-4.3] — acceptance criteria
- [Source: architecture.md#Dec-E-MCP-Server-Process-Model] — MCP spec documentation

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/mcp_server.py` — add version compatibility handling

**NEW:**
- `docs/mcp-setup.md`
