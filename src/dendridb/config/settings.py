from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

WorkingMemoryBackend = Literal["redis", "postgres"]
JobQueueBackend = Literal["celery", "sync"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DendriDB"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="dendridb", alias="POSTGRES_USER")
    postgres_password: str = Field(default="dendridb", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="dendridb", alias="POSTGRES_DB")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    working_memory_backend: WorkingMemoryBackend = Field(
        default="redis",
        alias="WORKING_MEMORY_BACKEND",
    )
    job_queue_backend: JobQueueBackend = Field(default="celery", alias="JOB_QUEUE_BACKEND")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="dendridb", alias="NEO4J_PASSWORD")

    embedding_dimensions: int = Field(default=384, alias="EMBEDDING_DIMENSIONS")
    embedding_model: str = Field(default="local-hash", alias="EMBEDDING_MODEL")

    decay_half_life_hours: float = Field(default=168.0, alias="DECAY_HALF_LIFE_HOURS")
    decay_min_salience: float = Field(default=0.1, alias="DECAY_MIN_SALIENCE")
    decay_max_salience: float = Field(default=10.0, alias="DECAY_MAX_SALIENCE")
    retrieval_strengthen_delta: float = Field(default=0.1, alias="RETRIEVAL_STRENGTHEN_DELTA")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def result_backend_url(self) -> str:
        if self.celery_result_backend:
            return self.celery_result_backend
        return f"redis://{self.redis_host}:{self.redis_port}/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
