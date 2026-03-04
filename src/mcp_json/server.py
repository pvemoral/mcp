"""MCP server entry point for mcp_json."""

import json
import logging
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .analyzer import describe_json, filter_array, query_json, search_json
from .models import DescribeJsonInput, FilterArrayInput, QueryJsonInput, SearchJsonInput

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

app = Server("mcp-json")

# ── Tool definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_json",
            description=(
                "Search for a text substring within a JSON string. "
                "Returns all matches with a context snippet around each match. "
                "Case-insensitive by default."
            ),
            inputSchema=SearchJsonInput.model_json_schema(),
        ),
        types.Tool(
            name="query_json",
            description=(
                "Evaluate a JSONPath expression against a JSON string and return all matching values. "
                "Examples: '$.items[*].name', '$.store.book[?(@.price < 10)]', '$..author'"
            ),
            inputSchema=QueryJsonInput.model_json_schema(),
        ),
        types.Tool(
            name="describe_json",
            description=(
                "Describe the structure and shape of a JSON document: "
                "top-level type, keys, array lengths, and nested schema up to max_depth."
            ),
            inputSchema=DescribeJsonInput.model_json_schema(),
        ),
        types.Tool(
            name="filter_array",
            description=(
                "Filter items in a JSON array by a field condition (key operator value). "
                "Operators: =, !=, >, <, >=, <=, contains, startswith. "
                "Use array_path to target a nested array via JSONPath."
            ),
            inputSchema=FilterArrayInput.model_json_schema(),
        ),
    ]


# ── Tool execution ────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info("Tool called: %s | args: %s", name, arguments)
    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, default=str, indent=2))]
    except (ValueError, KeyError) as exc:
        logger.warning("Tool %s raised expected error: %s", name, exc)
        return [types.TextContent(type="text", text=f"Error: {exc}")]
    except Exception as exc:
        logger.exception("Unexpected error in tool %s", name)
        return [types.TextContent(type="text", text=f"Unexpected error: {exc}")]


async def _dispatch(name: str, arguments: dict):
    if name == "search_json":
        return search_json(SearchJsonInput.model_validate(arguments))

    if name == "query_json":
        return query_json(QueryJsonInput.model_validate(arguments))

    if name == "describe_json":
        return describe_json(DescribeJsonInput.model_validate(arguments))

    if name == "filter_array":
        return filter_array(FilterArrayInput.model_validate(arguments))

    raise ValueError(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import asyncio
    asyncio.run(_run())


async def _run():
    logger.info("Starting mcp-json server")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
