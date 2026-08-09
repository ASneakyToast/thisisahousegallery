from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://cms:cms@localhost:5432/cms"
    debug: bool = False
    site_title: str = "This is a House Gallery"
    media_storage: str = "local"
    media_root: str = "media"
    media_url: str = "/media/"
    media_originals_dir: str = "originals"
    # S3 backend (used when MEDIA_STORAGE=s3)
    aws_region: str = "us-west-2"
    aws_s3_bucket: str = "housegallery-cms"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_base_url: str = ""


@lru_cache
def cached_settings() -> Settings:
    return Settings()


settings = cached_settings()
