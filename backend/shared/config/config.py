from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def detect_device(device: str) -> str:
    """Auto-detect device if set to 'auto'."""
    if device != "auto":
        return device

    import torch

    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


class LoggingSettings(BaseModel):
    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    DIR: Path = Field(default="logs", description="Path to log files directory")


class DatabaseSettings(BaseModel):
    USER: str = Field(default="postgres", description="Database username")
    PASSWORD: str = Field(default="postgres", description="Database password")
    HOST: str = Field(default="localhost", description="Database host")
    PORT: int = Field(default=5432, description="Database port")
    DB: str = Field(default="openfing_chat", description="Database name")
    VECTOR_STORE_COLLECTION: str = "chunks"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10

    @property
    def URL(self) -> PostgresDsn:
        """Construct Datbase Connection String."""
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


class DownloaderSettings(BaseModel):
    OUTPUT_DIR: Path = Field(default=Path("./audios"), description="Base directory for downloaded media files")
    WORKERS: int = Field(default=4, description="Number of concurrent workers", ge=1)
    CODEC: str = Field(default="best", description="Audio codec (best, mp3, m4a, etc.)")
    QUALITY: str = Field(default="0", description="Audio quality (0-10, 0=best)")


class ScraperSettings(BaseModel):
    WORKERS: int = Field(default=4, description="Number of concurrent workers", ge=1)
    OPENFING_URL: HttpUrl = Field(
        default="https://open.fing.edu.uy",
        description="OpenFIng base url",
    )


class TranscriberSettings(BaseModel):
    PORT: int = Field(default=8001, description="Server port")
    INPUT_DIR: Path = Field(
        default=Path("./audios"),
        description="Base path to look for audio files",
    )
    OUTPUT_DIR: Path = Field(default=Path("./transcriptions"), description="Directory to save transcription JSON files")


class EmbeddingsSettings(BaseModel):
    MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embeddings model name",
    )
    DIMENSION: int = Field(default=384, description="Embeddings dimensions")
    CACHE_DIR: Path | None = Field(default=None, description="Model cache directory")
    DEVICE: Literal["cpu", "cuda", "mps", "auto"] = Field(
        default="auto",
        description="Device to run embeddings on",
    )

    @model_validator(mode="after")
    def detect_device(self):
        self.DEVICE = detect_device(self.DEVICE)
        return self


class WhisperSettings(BaseModel):
    MODEL: str = Field(default="tiny", description="Whisper model name")
    CACHE_DIR: Path | None = Field(default=None, description="Model cache directory")
    DEVICE: Literal["cpu", "cuda", "mps", "auto"] = Field(
        default="auto",
        description="Device to run embeddings on",
    )

    @model_validator(mode="after")
    def detect_device(self):
        self.DEVICE = detect_device(self.DEVICE)
        return self


class PrefectSettings(BaseModel):
    API_URL: HttpUrl = Field(
        default="http://127.0.0.1:4200/api",
        description="Prefect API URL",
    )
    DB: str = Field(default="prefect", description="Prefect database name")


class Settings(BaseSettings):
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    LOG: LoggingSettings = Field(default_factory=LoggingSettings)
    WHISPER: WhisperSettings = Field(default_factory=WhisperSettings)
    EMBEDDINGS: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)
    DOWNLOADER: DownloaderSettings = Field(default_factory=DownloaderSettings)
    TRANSCRIBER: TranscriberSettings = Field(default_factory=TranscriberSettings)
    SCRAPER: ScraperSettings = Field(default_factory=ScraperSettings)
    PREFECT: PrefectSettings = Field(default_factory=PrefectSettings)

    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Basic app config
    APP_NAME: str = "Educational RAG"
    APP_DESCRIPTION: str = "RAG-powered educational content assistant"
    APP_VERSION: str = "v1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment settings
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS_COUNT: int = Field(
        default=3,
        description="Number of worker processes for production",
        ge=1,
    )

    FRONTEND_URL: HttpUrl = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS",
    )

    # External services
    HUGGINGFACE_API_KEY: str = Field(default="", description="Huggingface API key")

    LANGSMITH_TRACING: bool = Field(
        default=False,
        description="Enable LangSmith tracing",
        env="langsmith_tracing",
    )
    LANGSMITH_API_KEY: str = Field(description="LangSmith API key")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
        env_nested_delimiter="_",
    )

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
    return Settings()
