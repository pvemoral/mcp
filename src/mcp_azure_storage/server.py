"""MCP server entry point."""

import json
import logging
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .datalake import (
    get_file_info,
    list_filesystems,
    read_json_file,
    search_by_name,
    search_by_properties,
    write_json_file,
)
from .models import (
    GetFileInfoInput,
    ListFilesystemsInput,
    ReadJsonFileInput,
    SearchByNameInput,
    SearchByPropertiesInput,
    WriteJsonFileInput,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

app = Server("mcp-azure-storage")

# ── Tool definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_filesystems",
            description=(
                "List all containers (filesystems) available in the Azure Data Lake "
                "Storage account. No parameters required."
            ),
            inputSchema=ListFilesystemsInput.model_json_schema(),
        ),
        types.Tool(
            name="get_file_info",
            description=(
                "Get detailed metadata (size, extension, last modified, content type, etag) "
                "for a single file given its exact path inside a filesystem."
            ),
            inputSchema=GetFileInfoInput.model_json_schema(),
        ),
        types.Tool(
            name="search_files_by_name",
            description=(
                "Search files in the Data Lake by file name or glob pattern. "
                "Use '*' as a wildcard. The search is case-insensitive and also matches "
                "if the pattern is a plain substring of the file name. "
                "Examples: '*.parquet', 'sales_2024*', 'report'."
            ),
            inputSchema=SearchByNameInput.model_json_schema(),
        ),
        types.Tool(
            name="search_files_by_properties",
            description=(
                "Search files in the Data Lake by one or more file properties: "
                "extension, minimum/maximum size (bytes), and modification date range. "
                "All filters are optional and combined with AND logic."
            ),
            inputSchema=SearchByPropertiesInput.model_json_schema(),
        ),
        types.Tool(
            name="read_json_file",
            description=(
                "Download and return the parsed content of a JSON file from the Data Lake. "
                "Use max_size_kb to guard against reading unexpectedly large files."
            ),
            inputSchema=ReadJsonFileInput.model_json_schema(),
        ),
        types.Tool(
            name="write_json_file",
            description=(
                "Write or overwrite a JSON file in the Data Lake. "
                "The content must be a JSON object or array. "
                "Set overwrite=true to replace an existing file."
            ),
            inputSchema=WriteJsonFileInput.model_json_schema(),
        ),
    ]


# ── Tool execution ────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info("Tool called: %s | args: %s", name, arguments)

    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, default=str, indent=2))]
    except (ValueError, FileNotFoundError) as exc:
        logger.warning("Tool %s raised expected error: %s", name, exc)
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        logger.exception("Unexpected error in tool %s", name)
        return [types.TextContent(type="text", text=f"Unexpected error: {exc}")]


async def _dispatch(name: str, arguments: dict):
    if name == "list_filesystems":
        return list_filesystems()

    if name == "get_file_info":
        params = GetFileInfoInput.model_validate(arguments)
        info = get_file_info(params)
        return info.model_dump_display()

    if name == "search_files_by_name":
        params = SearchByNameInput.model_validate(arguments)
        files = search_by_name(params)
        return [f.model_dump_display() for f in files]

    if name == "search_files_by_properties":
        params = SearchByPropertiesInput.model_validate(arguments)
        files = search_by_properties(params)
        return [f.model_dump_display() for f in files]

    if name == "read_json_file":
        params = ReadJsonFileInput.model_validate(arguments)
        return read_json_file(params)

    if name == "write_json_file":
        params = WriteJsonFileInput.model_validate(arguments)
        return write_json_file(params)

    raise ValueError(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import asyncio
    asyncio.run(_run())


async def _run():
    logger.info("Starting mcp-azure-storage server")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
