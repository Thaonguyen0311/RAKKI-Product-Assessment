import secrets
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'development'
    app_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    cors_origins: str = 'http://localhost:5173'
    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_name: str = 'rakki'
    db_user: str = 'root'
    db_password: str = ''
    db_ssl_ca: str = ''
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-3.8-flash'
    max_upload_size_mb: int = 5
    storage_provider: str = 'local'
    storage_dir: str = 'storage'
    azure_storage_account_url: str = ''
    azure_storage_container: str = 'product-images'

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == 'production'

    @property
    def database_url(self) -> str:
        return (
            f'mysql+pymysql://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}'
            f'@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4'
        )

    @property
    def database_connect_args(self) -> dict:
        if not self.db_ssl_ca:
            return {}
        ca_path = Path(self.db_ssl_ca)
        if not ca_path.is_file():
            raise RuntimeError(f'DB_SSL_CA does not point to a readable PEM file: {ca_path}')
        return {
            'ssl_ca': str(ca_path),
            'ssl_verify_cert': True,
            'ssl_verify_identity': True,
        }

    @property
    def cors_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


settings = Settings()
