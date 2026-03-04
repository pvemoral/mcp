"""Pydantic input schemas for mcp_json tools."""

from typing import Literal

from pydantic import BaseModel, Field


class SearchJsonInput(BaseModel):
    content: str = Field(description="JSON content as a string.")
    query: str = Field(description="Text to search for within the JSON content.")
    case_sensitive: bool = Field(default=False, description="Case-sensitive search.")
    max_matches: int = Field(default=50, ge=1, le=500, description="Maximum number of matches to return.")


class QueryJsonInput(BaseModel):
    content: str = Field(description="JSON content as a string.")
    expression: str = Field(
        description="JSONPath expression. Examples: '$.items[*].name', '$.store.book[?(@.price < 10)]'"
    )


class DescribeJsonInput(BaseModel):
    content: str = Field(description="JSON content as a string.")
    max_depth: int = Field(default=5, ge=1, le=20, description="Maximum nesting depth to describe.")


class FilterArrayInput(BaseModel):
    content: str = Field(description="JSON content as a string. Root or nested value must be an array.")
    array_path: str = Field(
        default="$",
        description="JSONPath to the array to filter. Use '$' for root. Example: '$.items'",
    )
    key: str = Field(description="Field name to filter by within each array item.")
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "contains", "startswith"] = Field(
        default="=",
        description="Comparison operator.",
    )
    value: str = Field(description="Value to compare against. Will be coerced to match the field type.")
