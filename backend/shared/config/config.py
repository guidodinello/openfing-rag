from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    FILE_PATH: str = Field(default="logs", description="Path to log files directory")
    FILE_MAX_BYTES: int = Field(
        default=10_485_760,  # 10MB
        description="Maximum size of log file before rotation (in bytes)",
    )
    FILE_BACKUP_COUNT: int = Field(
        default=5,
        description="Number of backup files to keep",
    )

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")


class DatabaseSettings(BaseSettings):
    USER: str = Field(default="postgres", description="Datbase username")
    PASSWORD: str = Field(default="postgres", description="Datbase password")
    HOST: str = Field(default="localhost", description="Datbase host")
    PORT: int = Field(default=5432, description="Datbase port")
    DB: str = Field(default="openfing_chat", description="Datbase database name")
    ECHO: bool = False
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30

    DB_PREFECT: str = Field(default="prefect", description="Prefect database name")

    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="ignore")

    @property
    def URL(self) -> str:
        """Construct Datbase Connection String."""
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"

    @property
    def ASYNC_URL(self) -> str:
        # TODO: claude recommended, i dont know if its useful
        """Construct PostgreSQL URL with asyncpg driver."""
        return self.URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")


class WhisperSettings(BaseSettings):
    MODEL: str = Field(default="tiny", description="Whisper model name")
    model_config = SettingsConfigDict(env_prefix="WHISPER_", extra="ignore")


class EmbeddingsSettings(BaseSettings):
    MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embeddings model name",
    )
    DIMENSION: int = Field(default=384, description="Embeddings dimensions")
    CACHE_DIR: None | str = Field(default=None, description="Model cache directory")
    BATCH_SIZE: int = Field(
        default=32,
        description="""Number of texts to process in parallel.
        Increase if you have more GPU memory.""",
        ge=1,
    )
    DEVICE: Literal["cpu", "cuda"] = Field(
        default="cpu",
        description="Device to run embeddings on",
    )

    model_config = SettingsConfigDict(env_prefix="EMBEDDINGS_", extra="ignore")


class Settings(BaseSettings):
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    LOG: LoggingSettings = Field(default_factory=LoggingSettings)
    WHISPER: WhisperSettings = Field(default_factory=WhisperSettings)
    EMBEDDINGS: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)

    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Basic app config
    APP_NAME: str = "Educational RAG"
    APP_DESCRIPTION: str = "RAG-powered educational content assistant"
    API_V1_STR: str = "/api/v1"

    # Environment settings
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS_COUNT: int = Field(
        default=1,
        description="Number of worker processes for production",
        ge=1,
    )

    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-for-dev",
        description="Secret key for cryptographic signing",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Minutes before JWT tokens expire",
    )

    # CORS settings
    FRONTEND_URL: HttpUrl = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS",
    )
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="List of allowed hosts",
    )

    # Vector store settings
    VECTOR_STORE_COLLECTION: str = "rag_chunks"

    # External services
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    HUGGINGFACE_API_KEY: str = Field(default="", description="Huggingface API key")

    # Prefect settings
    PREFECT_API_URL: HttpUrl = Field(
        default="http://127.0.0.1:4200/api",
        description="Prefect API URL",
    )

    LANGSMITH_TRACING: bool = Field(
        default=False,
        description="Enable LangSmith tracing",
        env="langsmith_tracing",
    )
    LANGSMITH_API_KEY: str = Field(description="LangSmith API key")

    # Configuration for environment variables
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    def __init__(self, *args, **kwargs):
        _env_file = kwargs.get("_env_file")
        kwargs["DATABASE"] = DatabaseSettings(_env_file=_env_file)
        kwargs["LOG"] = LoggingSettings(_env_file=_env_file)
        kwargs["WHISPER"] = WhisperSettings(_env_file=_env_file)
        kwargs["EMBEDDINGS"] = EmbeddingsSettings(_env_file=_env_file)
        super().__init__(*args, **kwargs)

    @model_validator(mode="before")
    @classmethod
    def validate_env_file(cls, values: dict[str, Any]) -> dict[str, Any]:
        env_file = Path(".env")
        if not env_file.is_file():
            msg = f"""{env_file.absolute()} file not found!
            Please create one based on '.env.example'"""
            raise ValueError(msg)
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=".env")
