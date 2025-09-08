from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "NequiBot Chat Message API"
    debug: bool = False
    database_url: str = "sqlite:///./app.db"
    api_prefix: str = "/api"
    # Optional simple API key auth; if empty, auth is disabled
    api_key: str = ""
    # Comma-separated list of banned words for simple filtering
    banned_words: str = "foo,bar,baz"
    # Optional naive rate limit per minute (per API key or client host). 0 disables it.
    rate_limit_per_min: int = 0

    model_config = SettingsConfigDict(env_prefix="NEQUI_", env_file=".env", env_file_encoding="utf-8")


settings = Settings()
