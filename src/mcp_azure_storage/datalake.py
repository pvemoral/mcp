"""Business logic: querying Azure Data Lake Storage Gen2."""

import fnmatch
import json
import os
from datetime import datetime, timezone

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.filedatalake import FileSystemClient

from .client import get_blob_service_client, get_service_client
from .config import settings
from .models import (
    FileInfo,
    GetFileInfoInput,
    ReadJsonFileInput,
    SearchByNameInput,
    SearchByPropertiesInput,
    WriteJsonFileInput,
)


def _resolve_filesystem(filesystem: str | None) -> str:
    fs = filesystem or settings.default_filesystem
    if not fs:
        raise ValueError(
            "No filesystem specified and AZURE_STORAGE_FILESYSTEM is not set."
        )
    return fs


def _path_to_file_info(filesystem: str, item) -> FileInfo:
    """Convert an azure-sdk path item into a FileInfo model."""
    name = os.path.basename(item["name"].rstrip("/"))
    extension = os.path.splitext(name)[1].lstrip(".").lower() if not item.get("hdi_isfolder", False) else ""
    last_modified = None
    if item.get("last_modified"):
        lm = item["last_modified"]
        if isinstance(lm, datetime):
            last_modified = lm
        else:
            try:
                last_modified = datetime.fromisoformat(str(lm))
            except (ValueError, TypeError):
                last_modified = None

    return FileInfo(
        name=name,
        path=item["name"],
        filesystem=filesystem,
        size_bytes=item.get("content_length", 0) or 0,
        extension=extension,
        last_modified=last_modified,
        content_type=item.get("content_type"),
        etag=item.get("etag"),
        is_directory=item.get("hdi_isfolder", False),
    )


def _iter_paths(fs_client: FileSystemClient, path_prefix: str | None, recursive: bool):
    """Yield raw path items from the filesystem."""
    paths = fs_client.get_paths(path=path_prefix or "/", recursive=recursive)
    yield from paths


def list_filesystems() -> list[str]:
    client = get_service_client()
    return [fs["name"] for fs in client.list_file_systems()]


def get_file_info(params: GetFileInfoInput) -> FileInfo:
    filesystem = _resolve_filesystem(params.filesystem)
    client = get_service_client()
    fs_client = client.get_file_system_client(filesystem)

    try:
        file_client = fs_client.get_file_client(params.path)
        props = file_client.get_file_properties()
    except ResourceNotFoundError:
        raise FileNotFoundError(f"File not found: {params.path} in {filesystem}")

    # Build a dict compatible with _path_to_file_info
    item = {
        "name": params.path,
        "content_length": props.size,
        "last_modified": props.last_modified,
        "content_type": props.content_settings.content_type if props.content_settings else None,
        "etag": props.etag,
        "hdi_isfolder": props.metadata.get("hdi_isfolder", "false").lower() == "true"
        if props.metadata else False,
    }
    return _path_to_file_info(filesystem, item)


def search_by_name(params: SearchByNameInput) -> list[FileInfo]:
    filesystem = _resolve_filesystem(params.filesystem)
    client = get_service_client()
    fs_client = client.get_file_system_client(filesystem)

    pattern = params.name_pattern
    results: list[FileInfo] = []

    for item in _iter_paths(fs_client, params.path_prefix, params.recursive):
        if len(results) >= params.max_results:
            break

        raw = dict(item)
        name = os.path.basename(raw.get("name", "").rstrip("/"))

        # Skip directories unless the pattern explicitly targets them
        if raw.get("hdi_isfolder", False):
            continue

        if fnmatch.fnmatch(name.lower(), pattern.lower()) or pattern.lower() in name.lower():
            results.append(_path_to_file_info(filesystem, raw))

    return results


def read_json_file(params: ReadJsonFileInput) -> dict | list:
    filesystem = _resolve_filesystem(params.filesystem)
    blob_client = get_blob_service_client().get_blob_client(container=filesystem, blob=params.path)

    try:
        props = blob_client.get_blob_properties()
        size = props.size or 0
        max_bytes = params.max_size_kb * 1024
        if size > max_bytes:
            raise ValueError(
                f"File is {size // 1024} KB, exceeds limit of {params.max_size_kb} KB. "
                "Increase max_size_kb to read it."
            )
        return json.loads(blob_client.download_blob().readall())
    except ResourceNotFoundError:
        raise FileNotFoundError(f"File not found: {params.path} in {filesystem}")


def write_json_file(params: WriteJsonFileInput) -> dict:
    filesystem = _resolve_filesystem(params.filesystem)
    blob_client = get_blob_service_client().get_blob_client(container=filesystem, blob=params.path)

    content_bytes = json.dumps(params.content, ensure_ascii=False, indent=2).encode("utf-8")
    blob_client.upload_blob(
        content_bytes,
        overwrite=params.overwrite,
        content_type="application/json",
    )
    return {"path": params.path, "filesystem": filesystem, "bytes_written": len(content_bytes)}


def search_by_properties(params: SearchByPropertiesInput) -> list[FileInfo]:
    filesystem = _resolve_filesystem(params.filesystem)
    client = get_service_client()
    fs_client = client.get_file_system_client(filesystem)

    extensions = {e.lower().lstrip(".") for e in params.extensions} if params.extensions else None
    results: list[FileInfo] = []

    for item in _iter_paths(fs_client, params.path_prefix, params.recursive):
        if len(results) >= params.max_results:
            break

        raw = dict(item)
        if raw.get("hdi_isfolder", False):
            continue  # skip directories

        info = _path_to_file_info(filesystem, raw)

        # Filter by extension
        if extensions and info.extension not in extensions:
            continue

        # Filter by size
        if params.min_size_bytes is not None and info.size_bytes < params.min_size_bytes:
            continue
        if params.max_size_bytes is not None and info.size_bytes > params.max_size_bytes:
            continue

        # Filter by modification date
        if info.last_modified:
            lm = info.last_modified
            if lm.tzinfo is None:
                lm = lm.replace(tzinfo=timezone.utc)

            if params.modified_after:
                ma = params.modified_after
                if ma.tzinfo is None:
                    ma = ma.replace(tzinfo=timezone.utc)
                if lm < ma:
                    continue

            if params.modified_before:
                mb = params.modified_before
                if mb.tzinfo is None:
                    mb = mb.replace(tzinfo=timezone.utc)
                if lm > mb:
                    continue

        results.append(info)

    return results
