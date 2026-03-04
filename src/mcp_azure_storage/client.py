"""Azure Data Lake Storage Gen2 client factory."""

from functools import lru_cache

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from .config import settings


@lru_cache(maxsize=1)
def get_service_client() -> DataLakeServiceClient:
    """Return a cached DataLakeServiceClient using the best available credential."""
    url = settings.account_url

    # Priority 1: SAS token
    if settings.sas_token:
        return DataLakeServiceClient(
            account_url=url,
            credential=settings.sas_token,
        )

    # Priority 2: service principal
    if settings.tenant_id and settings.client_id and settings.client_secret:
        credential = ClientSecretCredential(
            tenant_id=settings.tenant_id,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
        )
        return DataLakeServiceClient(account_url=url, credential=credential)

    # Priority 3: DefaultAzureCredential (managed identity, az login, env vars…)
    return DataLakeServiceClient(
        account_url=url,
        credential=DefaultAzureCredential(),
    )
