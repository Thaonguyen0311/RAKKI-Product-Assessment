from functools import lru_cache
from pathlib import Path

from app.core.config import settings


def local_image_path(filename: str) -> Path:
    if Path(filename).name != filename or filename in {'', '.', '..'}:
        raise ValueError('Invalid image key')
    root = Path(settings.storage_dir).resolve()
    path = (root / filename).resolve()
    if path.parent != root:
        raise ValueError('Invalid image key')
    return path


@lru_cache(maxsize=1)
def _blob_service_client():
    if not settings.azure_storage_account_url:
        raise RuntimeError('AZURE_STORAGE_ACCOUNT_URL is required when STORAGE_PROVIDER=azure_blob')
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError('Azure Blob support dependencies are not installed') from exc
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return BlobServiceClient(account_url=settings.azure_storage_account_url, credential=credential)


def _blob(filename: str):
    if Path(filename).name != filename or filename in {'', '.', '..'}:
        raise ValueError('Invalid image key')
    return _blob_service_client().get_blob_client(
        container=settings.azure_storage_container,
        blob=filename,
    )


def save_image(filename: str, data: bytes, content_type: str) -> None:
    if settings.storage_provider == 'azure_blob':
        from azure.storage.blob import ContentSettings
        _blob(filename).upload_blob(
            data,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )
        return
    if settings.storage_provider != 'local':
        raise RuntimeError('STORAGE_PROVIDER must be local or azure_blob')
    path = local_image_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def get_image(filename: str) -> bytes:
    if settings.storage_provider == 'azure_blob':
        return _blob(filename).download_blob(max_concurrency=1).readall()
    return local_image_path(filename).read_bytes()


def image_exists(filename: str) -> bool:
    if settings.storage_provider == 'azure_blob':
        return _blob(filename).exists()
    return local_image_path(filename).is_file()


def delete_image(filename: str) -> None:
    if settings.storage_provider == 'azure_blob':
        from azure.core.exceptions import ResourceNotFoundError
        try:
            _blob(filename).delete_blob(delete_snapshots='include')
        except ResourceNotFoundError:
            pass
        return
    local_image_path(filename).unlink(missing_ok=True)
