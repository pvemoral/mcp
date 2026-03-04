"""Business logic: JSON analysis operations, origin-agnostic."""

import json

from jsonpath_ng import parse as jsonpath_parse

from .models import DescribeJsonInput, FilterArrayInput, QueryJsonInput, SearchJsonInput


def search_json(params: SearchJsonInput) -> dict:
    """Search for a text substring in JSON content and return matches with context snippets."""
    text = params.content
    query = params.query if params.case_sensitive else params.query.lower()
    haystack = text if params.case_sensitive else text.lower()

    matches = []
    start = 0
    while len(matches) < params.max_matches:
        idx = haystack.find(query, start)
        if idx == -1:
            break
        ctx_start = max(0, idx - 80)
        ctx_end = min(len(text), idx + len(params.query) + 80)
        snippet = ("..." if ctx_start > 0 else "") + text[ctx_start:ctx_end] + ("..." if ctx_end < len(text) else "")
        matches.append({"position": idx, "snippet": snippet})
        start = idx + 1

    return {"query": params.query, "total_matches": len(matches), "results": matches}


def query_json(params: QueryJsonInput) -> dict:
    """Evaluate a JSONPath expression against JSON content."""
    data = json.loads(params.content)
    expr = jsonpath_parse(params.expression)
    results = [match.value for match in expr.find(data)]
    return {"expression": params.expression, "count": len(results), "results": results}


def _describe_value(value, depth: int, max_depth: int):
    """Recursively build a schema description of a JSON value."""
    if depth >= max_depth:
        if isinstance(value, dict):
            return f"object({len(value)} keys)"
        if isinstance(value, list):
            return f"array({len(value)} items)"
        return type(value).__name__

    if isinstance(value, dict):
        return {k: _describe_value(v, depth + 1, max_depth) for k, v in value.items()}

    if isinstance(value, list):
        if not value:
            return "array(empty)"
        sample = _describe_value(value[0], depth + 1, max_depth)
        return {"_type": "array", "_length": len(value), "_item_schema": sample}

    if value is None:
        return "null"

    return type(value).__name__


def describe_json(params: DescribeJsonInput) -> dict:
    """Describe the structure and shape of a JSON document."""
    data = json.loads(params.content)
    result = {
        "type": type(data).__name__,
        "schema": _describe_value(data, 0, params.max_depth),
    }
    if isinstance(data, list):
        result["length"] = len(data)
    elif isinstance(data, dict):
        result["keys"] = list(data.keys())
    return result


def filter_array(params: FilterArrayInput) -> dict:
    """Filter items in a JSON array by a key/operator/value condition."""
    data = json.loads(params.content)

    if params.array_path == "$":
        arr = data
    else:
        expr = jsonpath_parse(params.array_path)
        found = expr.find(data)
        if not found:
            raise ValueError(f"Path '{params.array_path}' not found in JSON.")
        arr = found[0].value

    if not isinstance(arr, list):
        raise ValueError(f"Value at '{params.array_path}' is not an array (got {type(arr).__name__}).")

    def coerce(field_val, str_val: str):
        if isinstance(field_val, bool):
            return str_val.lower() in ("true", "1", "yes")
        if isinstance(field_val, int):
            return int(str_val)
        if isinstance(field_val, float):
            return float(str_val)
        return str_val

    results = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        field_val = item.get(params.key)
        if field_val is None:
            continue
        try:
            cmp_val = coerce(field_val, params.value)
        except (ValueError, TypeError):
            continue

        op = params.operator
        if op == "=" and field_val == cmp_val:
            results.append(item)
        elif op == "!=" and field_val != cmp_val:
            results.append(item)
        elif op == ">" and field_val > cmp_val:
            results.append(item)
        elif op == "<" and field_val < cmp_val:
            results.append(item)
        elif op == ">=" and field_val >= cmp_val:
            results.append(item)
        elif op == "<=" and field_val <= cmp_val:
            results.append(item)
        elif op == "contains" and isinstance(field_val, str) and params.value.lower() in field_val.lower():
            results.append(item)
        elif op == "startswith" and isinstance(field_val, str) and field_val.lower().startswith(params.value.lower()):
            results.append(item)

    return {"total_in_array": len(arr), "matches": len(results), "results": results}
