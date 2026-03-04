# MCP Azure Data Lake Storage

MCP server that lets any MCP-compatible client (Claude Desktop, Continue, etc.) discover and inspect files stored in **Azure Data Lake Storage Gen2**.

---

## Tools available

| Tool | Description |
|---|---|
| `list_filesystems` | List all containers in the storage account |
| `get_file_info` | Get full metadata for a single file by exact path |
| `search_files_by_name` | Find files by name substring or glob pattern (`*`) |
| `search_files_by_properties` | Find files by extension, size range, and/or modification date |

---

## Credentials

### Required

| Variable | Description |
|---|---|
| `AZURE_STORAGE_ACCOUNT_NAME` | Name of the storage account (e.g. `mystorageaccount`) |

### Authentication (choose ONE method)

**Option A – SAS Token** (scoped, time-limited)

```
AZURE_STORAGE_SAS_TOKEN=?sv=2023-...&sig=...
```

Generate it from: Azure Portal → Storage Account → **Security + networking → Shared access signature**
Grant at least: *Service: Blob/DFS*, *Resource types: Container + Object*, *Permissions: Read + List*.

---

**Option B – Service Principal** (recommended for production)

```
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-app-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
```

Steps:
1. Azure Portal → **Azure Active Directory → App registrations → New registration**
2. Create a client secret under **Certificates & secrets**
3. Go to your Storage Account → **Access Control (IAM) → Add role assignment**
4. Assign the role **Storage Blob Data Reader** to your app registration

---

**Option C – DefaultAzureCredential** (managed identity / `az login`)

Leave all variables above empty. The SDK will automatically try, in order:
- Managed Identity
- Azure CLI (`az login`)
- Visual Studio Code

---

### Optional

| Variable | Description |
|---|---|
| `AZURE_STORAGE_FILESYSTEM` | Default container/filesystem when tools omit `filesystem` |

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd mcp

# 2. Create virtual environment
python -m venv .venv

# 3. Install the package in editable mode (run from the repo root)
.venv\Scripts\pip install -e .   # Windows
# .venv/bin/pip install -e .     # macOS/Linux

# 4. Verify the install
.venv\Scripts\python.exe -c "import mcp_azure_storage; print(mcp_azure_storage.__file__)"
# Expected: ...\mcp\src\mcp_azure_storage\__init__.py
```

No se usa `.env`. Las credenciales se pasan directamente desde la configuración del cliente MCP.

> **Troubleshooting – `No module named 'mcp_azure_storage'`**
>
> El install editable crea un archivo `.pth` en el venv que apunta al directorio `src/`.
> Si tienes varios proyectos en la misma carpeta y has ejecutado `pip install -e .` desde el directorio equivocado, ese archivo puede apuntar a la ruta incorrecta.
>
> Comprueba el contenido del archivo:
> ```
> .venv\Lib\site-packages\_mcp_azure_storage.pth
> ```
> Debe contener la ruta absoluta a `mcp\src` (p. ej. `C:\projects\personal\mcp\src`).
> Si apunta a otro directorio, corrígelo manualmente o reinstala ejecutando `pip install -e .` **desde la raíz del repositorio** (`mcp/`).

---

## Claude Desktop integration

Las credenciales van en el bloque `env` de cada entrada en `claude_desktop_config.json`.
**El mismo servidor sirve para múltiples storage accounts** añadiendo una entrada por cuenta:

```json
{
  "mcpServers": {
    "datalake-produccion": {
      "command": "/path/to/mcp/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_azure_storage.server"],
      "env": {
        "AZURE_STORAGE_ACCOUNT_NAME": "prodstorageaccount",
        "AZURE_TENANT_ID": "a1b2c3d4-...",
        "AZURE_CLIENT_ID": "b2c3d4e5-...",
        "AZURE_CLIENT_SECRET": "xK8~vP2m...",
        "AZURE_STORAGE_FILESYSTEM": "raw"
      }
    },
    "datalake-desarrollo": {
      "command": "/path/to/mcp/.venv/Scripts/python.exe",
      "args": ["-m", "mcp_azure_storage.server"],
      "env": {
        "AZURE_STORAGE_ACCOUNT_NAME": "devstorageaccount",
        "AZURE_STORAGE_SAS_TOKEN": "?sv=2023-...&sig=...",
        "AZURE_STORAGE_FILESYSTEM": "landing"
      }
    }
  }
}
```

> **Windows**: usa doble backslash `\\` en las rutas y `.venv\\Scripts\\python.exe`.
> **macOS/Linux**: usa `.venv/bin/python` y rutas con `/`.

---

## Example prompts

```
List all containers in the storage account.

Find all parquet files under the "raw/orders" folder.

Search for files modified in the last 7 days larger than 10 MB.

Get the metadata for the file raw/orders/2024/01/orders.parquet.
```

---

## Architecture

```
src/mcp_azure_storage/
├── __init__.py     # package version
├── config.py       # settings from env vars
├── client.py       # DataLakeServiceClient factory (cached)
├── models.py       # Pydantic models for file metadata & tool inputs
├── datalake.py     # business logic (list, search, get)
└── server.py       # MCP server, tool definitions & dispatch
```

### Credential priority (client.py)

1. SAS Token
2. Service Principal
3. DefaultAzureCredential (managed identity, az login, …)
