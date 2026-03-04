"""Azure Data Lake Storage Gen2 client factory."""

from functools import lru_cache

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.storage.filedatalake import DataLakeServiceClient

from .config import settings


def _credential():
    """Build the best available credential (shared by both clients)."""
    if settings.sas_token:
        return settings.sas_token
    if settings.tenant_id and settings.client_id and settings.client_secret:
        return ClientSecretCredential(
            tenant_id=settings.tenant_id,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
        )
    return DefaultAzureCredential()


@lru_cache(maxsize=1)
def get_service_client() -> DataLakeServiceClient:
    """Return a cached DataLakeServiceClient (DFS endpoint) for read/list operations."""
    return DataLakeServiceClient(account_url=settings.account_url, credential=_credential())


@lru_cache(maxsize=1)
def get_blob_service_client() -> BlobServiceClient:
    """Return a cached BlobServiceClient (Blob endpoint) for write operations."""
    blob_url = settings.account_url.replace(".dfs.", ".blob.")
    return BlobServiceClient(account_url=blob_url, credential=_credential())
