"""Configuration from environment variables injected by the MCP client."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    account_name: str
    sas_token: str | None
    tenant_id: str | None
    client_id: str | None
    client_secret: str | None
    default_filesystem: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "")
        if not account_name:
            raise ValueError(
                "AZURE_STORAGE_ACCOUNT_NAME environment variable is required"
            )
        return cls(
            account_name=account_name,
            sas_token=os.environ.get("AZURE_STORAGE_SAS_TOKEN"),
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET"),
            default_filesystem=os.environ.get("AZURE_STORAGE_FILESYSTEM"),
        )

    @property
    def account_url(self) -> str:
        return f"https://{self.account_name}.dfs.core.windows.net"


settings = Settings.from_env()
