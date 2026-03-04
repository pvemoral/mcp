# MCP Servers

Collection of Python MCP (Model Context Protocol) servers for use with any MCP-compatible client (Claude Desktop, Continue, etc.).

---

## Servers

| Server | Description |
|---|---|
| [`mcp_azure_storage`](src/mcp_azure_storage/README.md) | Discover, inspect, read and write files in Azure Data Lake Storage Gen2 |
| [`mcp_json`](src/mcp_json/README.md) | Analyse JSON content: search, JSONPath queries, describe structure, filter arrays |

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd mcp

# Create virtual environment and install all servers
python -m venv .venv
.venv/Scripts/pip install -e .   # Windows
# .venv/bin/pip install -e .     # macOS/Linux
```

See each server's README for credentials, configuration, and Claude Desktop integration details.
