from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Magnetly API'
    debug: bool = True
    database_url: str
    google_api_key: str | None = None
    hf_model_name: str = 'distilbert/distilbert-base-uncased-finetuned-sst-2-english'
    cors_origins: str = 'http://localhost:3000'

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
