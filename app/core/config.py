from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@db:5432/stageflow"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    debug: bool = False
    app_name: str = "StageFlow API"
    api_v1_prefix: str = "/api/v1"
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()