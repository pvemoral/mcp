"""Pydantic models for file metadata and tool inputs."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    name: str
    path: str
    filesystem: str
    size_bytes: int
    extension: str
    last_modified: datetime | None
    content_type: str | None
    etag: str | None
    is_directory: bool

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 2)

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / (1024 * 1024), 4)

    def model_dump_display(self) -> dict:
        d = self.model_dump()
        d["size_kb"] = self.size_kb
        d["size_mb"] = self.size_mb
        return d


# ── Tool input schemas ────────────────────────────────────────────────────────

class SearchByNameInput(BaseModel):
    name_pattern: str = Field(
        description=(
            "Substring or glob-style pattern to match against file names. "
            "Use '*' as wildcard. Example: '*.parquet', 'sales_2024'"
        )
    )
    filesystem: str | None = Field(
        default=None,
        description="Container / filesystem name. Uses AZURE_STORAGE_FILESYSTEM if omitted.",
    )
    path_prefix: str | None = Field(
        default=None,
        description="Directory path prefix to restrict the search. Example: 'raw/orders'",
    )
    recursive: bool = Field(
        default=True,
        description="Search subdirectories recursively.",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of results to return.",
    )


class SearchByPropertiesInput(BaseModel):
    filesystem: str | None = Field(
        default=None,
        description="Container / filesystem name. Uses AZURE_STORAGE_FILESYSTEM if omitted.",
    )
    path_prefix: str | None = Field(
        default=None,
        description="Directory path prefix to restrict the search.",
    )
    extensions: list[str] | None = Field(
        default=None,
        description="List of file extensions to include, without dot. Example: ['csv', 'parquet']",
    )
    min_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Minimum file size in bytes (inclusive).",
    )
    max_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Maximum file size in bytes (inclusive).",
    )
    modified_after: datetime | None = Field(
        default=None,
        description="Only return files modified after this UTC datetime (ISO 8601).",
    )
    modified_before: datetime | None = Field(
        default=None,
        description="Only return files modified before this UTC datetime (ISO 8601).",
    )
    recursive: bool = Field(
        default=True,
        description="Search subdirectories recursively.",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of results to return.",
    )


class ListFilesystemsInput(BaseModel):
    pass  # no parameters needed


class GetFileInfoInput(BaseModel):
    filesystem: str | None = Field(
        default=None,
        description="Container / filesystem name. Uses AZURE_STORAGE_FILESYSTEM if omitted.",
    )
    path: str = Field(
        description="Full path of the file within the filesystem.",
    )


SizeUnit = Literal["bytes", "kb", "mb"]
