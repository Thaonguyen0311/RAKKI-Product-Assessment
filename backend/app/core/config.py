from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    app_env: str = 'development'
    app_secret_key: str = 'development-only-change-me'
    cors_origins: str = 'http://localhost:5173'
    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_name: str = 'rakki'
    db_user: str = 'rakki_app'
    db_password: str = ''
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    max_upload_size_mb: int = 5
    storage_dir: str = 'storage'

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        return f'mysql+pymysql://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4'

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]

settings = Settings()
