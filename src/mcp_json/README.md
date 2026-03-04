# MCP JSON

MCP server for analysing JSON content. Origin-agnostic: works with any JSON string regardless of where it came from (Data Lake, API, local file, etc.).

---

## Tools available

| Tool | Description |
|---|---|
| `search_json` | Search for a text substring within JSON content. Returns matches with context snippets. |
| `query_json` | Evaluate a JSONPath expression and return all matching values. |
| `describe_json` | Describe the structure: top-level type, keys, array lengths, nested schema. |
| `filter_array` | Filter items in a JSON array by a `key operator value` condition. |

---

## Tool reference

### `search_json`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `content` | string | required | JSON content as a string |
| `query` | string | required | Text to search for |
| `case_sensitive` | bool | `false` | Case-sensitive match |
| `max_matches` | int | `50` | Maximum matches to return |

### `query_json`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `content` | string | required | JSON content as a string |
| `expression` | string | required | JSONPath expression, e.g. `$.items[*].name` |

### `describe_json`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `content` | string | required | JSON content as a string |
| `max_depth` | int | `5` | Maximum nesting depth to describe |

### `filter_array`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `content` | string | required | JSON content as a string |
| `array_path` | string | `$` | JSONPath to the target array (`$` = root) |
| `key` | string | required | Field name to filter by |
| `operator` | string | `=` | One of: `=` `!=` `>` `<` `>=` `<=` `contains` `startswith` |
| `value` | string | required | Value to compare against |

---

## Setup

```bash
# From the repo root
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .   # Windows
# .venv/bin/python -m pip install -e .          # macOS/Linux

# Verify
.venv\Scripts\python.exe -c "import mcp_json; print('OK')"
```

No credentials required — this server operates purely on JSON strings passed as tool arguments.

---

## Claude Desktop integration

```json
{
  "mcpServers": {
    "json": {
      "command": "C:\\projects\\personal\\mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_json.server"]
    }
  }
}
```

---

## Typical workflow with mcp_azure_storage

1. Use `mcp_azure_storage` → `read_json_file` to download a file from the Data Lake.
2. Pass the returned JSON string to any `mcp_json` tool for analysis.
3. Optionally use `mcp_azure_storage` → `write_json_file` to save results back.

---

## Example prompts

```
Describe the structure of this JSON: <paste JSON>

Find all values where "status" equals "active" in the items array.

Query $.orders[*].total from this JSON and sum the results.

Search for the text "error" in this JSON response.
```

---

## Architecture

```
src/mcp_json/
├── __init__.py     # package version
├── models.py       # Pydantic input schemas
├── analyzer.py     # business logic (search, query, describe, filter)
└── server.py       # MCP server, tool definitions & dispatch
```
