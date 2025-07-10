from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from shared.utils import detect_device, parse_comma_separated_list


class LoggingSettings(BaseModel):
    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    DIR: Path = Field(default=Path("./default_logs"), description="Path to log files directory")


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
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


class DownloaderSettings(BaseModel):
    OUTPUT_DIR: Path = Field(
        default=Path("./default_audios"),
        description="Base directory for downloaded media files",
    )
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
    INPUT_DIR: Path = Field(
        default=Path("./default_audios"),
        description="Base path to look for audio files",
    )
    OUTPUT_DIR: Path = Field(
        default=Path("./default_transcriptions"),
        description="Directory to save transcription JSON files",
    )


class EmbeddingsSettings(BaseModel):
    MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embeddings model name",
    )
    DIMENSION: int = Field(default=384, description="Embeddings dimensions")
    CACHE_DIR: Path | None = Field(default=Path("./default_models_cache"), description="Model cache directory")
    DEVICE: Literal["cpu", "cuda", "mps", "auto"] = Field(
        default="auto",
        description="Device to run embeddings on",
    )

    @field_validator("DEVICE", mode="after")
    @classmethod
    def detect_device(cls, v: str) -> str:
        return detect_device(v)


class WhisperSettings(BaseModel):
    MODEL: str = Field(default="tiny", description="Whisper model name")
    CACHE_DIR: Path | None = Field(default=Path("./default_models_cache"), description="Model cache directory")
    DEVICE: Literal["cpu", "cuda", "mps", "auto"] = Field(
        default="auto",
        description="Device to run whisper on",
    )

    @field_validator("MODEL", mode="after")
    @classmethod
    def validate_model(cls, v: str) -> str:
        import whisper

        available_models = whisper.available_models()
        if v not in available_models:
            raise ValueError(
                f"WHISPER_MODEL should be one of {', '.join(sorted(available_models))}\
            if its there and still fails please add it to our WhisperModelSize enum",
            )
        return v

    @field_validator("DEVICE", mode="after")
    @classmethod
    def detect_device(cls, v: str) -> str:
        return detect_device(v)


class PrefectSettings(BaseModel):
    API_URL: HttpUrl = Field(
        default="http://127.0.0.1:4200/api",
        description="Prefect API URL",
    )
    DB: str = Field(default="prefect", description="Prefect database name")


class ApiKeys(BaseModel):
    ADMIN: Annotated[list[str], NoDecode] = Field(default_factory=list, description="Comma-separated admin API keys")
    READ: Annotated[list[str], NoDecode] = Field(default_factory=list, description="Comma-separated read-only API keys")
    WRITE: Annotated[list[str], NoDecode] = Field(default_factory=list, description="Comma-separated write API keys")

    @field_validator("ADMIN", "READ", "WRITE", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str | list[str]) -> list[str]:
        if not isinstance(v, str):
            return []
        return parse_comma_separated_list(v)

    @property
    def all(self) -> set[str]:
        return set(self.ADMIN + self.READ + self.WRITE)


class ServerSettings(BaseModel):
    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS_COUNT: int = Field(
        default=3,
        description="Number of worker processes for production",
        ge=1,
    )


class HuggingFaceSettings(BaseModel):
    API_KEY: str = Field(default="NOT_SET", description="Huggingface API key")


class LangsmithSettings(BaseModel):
    API_KEY: str = Field(default="NOT_SET", description="LangSmith API key")
    TRACING: bool = Field(
        default=False,
        description="Enable LangSmith tracing",
    )


class AppSettings(BaseModel):
    # Basic app config
    NAME: str = Field(default="Educational RAG", description="Application name")
    DESCRIPTION: str = Field(default="RAG-powered educational content assistant", description="Application description")
    VERSION: str = Field(description="Application version")
    ENV: Literal["local", "production"] = Field(..., descriptions="Environment in which the app is running")


class Settings(BaseSettings):
    APP: AppSettings = Field(default_factory=AppSettings)
    API_KEYS: ApiKeys = Field(default_factory=ApiKeys)
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    LOG: LoggingSettings = Field(default_factory=LoggingSettings)
    SERVER: ServerSettings = Field(default_factory=ServerSettings)

    WHISPER: WhisperSettings = Field(default_factory=WhisperSettings)
    EMBEDDINGS: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)

    PREFECT: PrefectSettings = Field(default_factory=PrefectSettings)
    HUGGINGFACE: HuggingFaceSettings = Field(default_factory=HuggingFaceSettings)
    LANGSMITH: LangsmithSettings = Field(default_factory=LangsmithSettings)

    DOWNLOADER: DownloaderSettings = Field(default_factory=DownloaderSettings)
    TRANSCRIBER: TranscriberSettings = Field(default_factory=TranscriberSettings)
    SCRAPER: ScraperSettings = Field(default_factory=ScraperSettings)

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # API Documentation URLs
    API_V1_URL: str = Field(default="/api/v1", description="API v1 prefix path")
    DOCS_URL: str | None = Field(default="/docs", description="Swagger UI documentation endpoint")
    REDOC_URL: str | None = Field(default="/redoc", description="ReDoc documentation endpoint")
    OPENAPI_URL: str | None = Field(default="/openapi.json", description="OpenAPI JSON schema endpoint")
    HEALTH_URL: str = Field(default="/health", description="Healthcheck endpoint")

    FRONTEND_URL: HttpUrl = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="forbid",
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
