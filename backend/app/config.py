from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    aiops_env: str = "dev"
    database_url: str = "sqlite:///./aiops.db"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "aiops-logs"

    llm_provider: str = "none"  # none | openai | dashscope | zhipu 等（OpenAI 兼容）
    llm_api_base: str | None = None  # 如 https://api.openai.com/v1
    llm_api_key: str | None = None
    llm_model: str = "gpt-3.5-turbo"  # 如 gpt-4、qwen-turbo、glm-4-flash


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

