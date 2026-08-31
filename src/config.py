from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        env_prefix="RECIPES_"
    )

    database_url: str = "sqlite+pysqlite:///./recipes.db"
    debug: bool = False
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

@lru_cache
def get_settings() -> Settings:
    return Settings()
