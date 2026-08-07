from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cms:cms@localhost:5432/cms"
    debug: bool = False
    site_title: str = "This is a House Gallery"


@lru_cache
def cached_settings() -> Settings:
    return Settings()


settings = cached_settings()
