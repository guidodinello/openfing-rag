from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    EmailStr,
    Field,
    HttpUrl,
    PositiveInt,
    PostgresDsn,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.enums import LLMProvider
from shared.enums.devices import Devices
from shared.utils import detect_device


class LoggingSettings(BaseModel):
    LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    DIR: DirectoryPath = Field(
        default=Path("./default_logs"),
        description="Path to log files directory",
    )


class DatabaseSettings(BaseModel):
    USER: str = Field(default="postgres", description="Database username")
    PASSWORD: SecretStr = Field(default="postgres", description="Database password")
    HOST: str = Field(default="localhost", description="Database host")
    PORT: int = Field(default=5432, description="Database port")
    DB: str = Field(default="openfing_chat", description="Database name")
    VECTOR_STORE_COLLECTION: str = Field(
        default="chunks",
        description="Vector Store collection name",
    )
    POOL_SIZE: int = Field(default=5, description="")
    MAX_OVERFLOW: int = Field(default=10, description="")

    @property
    def URL(self) -> PostgresDsn:
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD.get_secret_value()}@{self.HOST}:{self.PORT}/{self.DB}"


class PromptsSettings(BaseModel):
    BASE_DIR: DirectoryPath = Field(
        default=Path("./default_prompts"),
        description="Base directory for prompt template files",
    )
    GENERATOR_TEMPLATE: str = Field(
        default="educational_assistant",
        description="Filename for the generator prompt template",
    )
    TRANSCRIBER_TEMPLATE: str = Field(
        default="educational_transcription",
        description="Filename for the transcriber prompt template",
    )


class OllamaSettings(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name.lower(), populate_by_name=True)

    BASE_URL: HttpUrl = Field(examples=["http://localhost:11434"], description="Ollama API URL")
    MODEL: str = Field(examples=["qwen2.5:0.5b"], description="Ollama model identifier")


class HuggingFaceSettings(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name.lower(), populate_by_name=True)

    API_KEY: SecretStr = Field(description="Huggingface API key")
    MODEL: str = Field(
        examples=["mistralai/Mistral-7B-Instruct-v0.3"],
        description="Huggingface LLM used for chat completion",
    )


class LLMSettings(BaseModel):
    PROVIDER: LLMProvider = Field(default=LLMProvider.HUGGINGFACE, description="LLM provider to use")
    OLLAMA: OllamaSettings | None = Field(default=None)
    HUGGINGFACE: HuggingFaceSettings | None = Field(default=None)

    @model_validator(mode="after")
    def validate_provider_config(self):
        if self.PROVIDER == LLMProvider.OLLAMA and self.OLLAMA is None:
            raise ValueError(f"OLLAMA settings must be provided when PROVIDER is {LLMProvider.OLLAMA}")
        if self.PROVIDER == LLMProvider.HUGGINGFACE and self.HUGGINGFACE is None:
            raise ValueError(f"HUGGINGFACE settings must be provided when PROVIDER is {LLMProvider.HUGGINGFACE}")
        return self


class DownloaderSettings(BaseModel):
    OUTPUT_DIR: DirectoryPath = Field(
        default=Path("./default_audios"),
        description="Base directory for downloaded media files",
    )
    WORKERS: PositiveInt = Field(default=4, description="Number of concurrent workers")
    CODEC: str = Field(default="best", description="Audio codec (best, mp3, m4a, etc.)")
    QUALITY: str = Field(default="0", description="Audio quality (0-10, 0=best)")


class ScraperSettings(BaseModel):
    WORKERS: PositiveInt = Field(default=4, description="Number of concurrent workers")
    OPENFING_URL: HttpUrl = Field(
        default=HttpUrl("https://open.fing.edu.uy"),
        description="OpenFIng base url",
    )


class TranscriberSettings(BaseModel):
    INPUT_DIR: DirectoryPath = Field(
        default=Path("./default_audios"),
        description="Base path to look for audio files",
    )
    OUTPUT_DIR: DirectoryPath = Field(
        default=Path("./default_transcriptions"),
        description="Directory to save transcription JSON files",
    )


class EmbeddingsSettings(BaseModel):
    MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embeddings model name",
    )
    DIMENSION: int = Field(default=384, description="Embeddings dimensions")
    CACHE_DIR: DirectoryPath | None = Field(
        default=Path("./default_models_cache"),
        description="Model cache directory",
    )
    DEVICE: Devices = Field(
        default=Devices.AUTO,
        description="Device to run embeddings on",
    )

    @field_validator("DEVICE", mode="after")
    @classmethod
    def detect_device(cls, v: str) -> str:
        return detect_device(v)


class WhisperSettings(BaseModel):
    MODEL: str = Field(default="tiny", description="Whisper model name")
    CACHE_DIR: DirectoryPath | None = Field(
        default=Path("./default_models_cache"),
        description="Model cache directory",
    )
    DEVICE: Devices = Field(
        default=Devices.AUTO,
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
        default=HttpUrl("http://127.0.0.1:4200/api"),
        description="Prefect API URL",
    )
    DB: str = Field(default="prefect", description="Prefect database name")


class ApiKeys(BaseModel):
    HMAC_SECRET: SecretStr = Field(
        default="NOT_SET",
        description="HMAC secret for API key hashing",
        min_length=32,
    )


class ServerSettings(BaseModel):
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS_COUNT: int = Field(
        default=3,
        description="Number of worker processes for production",
        ge=1,
    )


class LangsmithSettings(BaseModel):
    API_KEY: SecretStr = Field(default="NOT_SET", description="LangSmith API key")
    TRACING: bool = Field(
        default=False,
        description="Enable LangSmith tracing",
    )


class JwtSettings(BaseModel):
    SECRET_KEY: SecretStr = Field(
        default="NOT_SET",
        description="Secret key for JWT token signing",
        min_length=32,
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration time in days")
    TOKEN_URL: str = Field(default="/token", description="")


class AppSettings(BaseModel):
    NAME: str = Field(default="Educational RAG", description="Application name")
    DESCRIPTION: str = Field(
        default="RAG-powered educational content assistant",
        description="Application description",
    )
    VERSION: str = Field(description="Application version")
    ENV: Literal["local", "production", "cluster"] = Field(
        ...,
        descriptions="Environment in which the app is running",
    )


class Settings(BaseSettings):
    APP: AppSettings = Field(default_factory=AppSettings)
    API_KEYS: ApiKeys = Field(default_factory=ApiKeys)
    JWT: JwtSettings = Field(default_factory=JwtSettings)
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    LOG: LoggingSettings = Field(default_factory=LoggingSettings)
    SERVER: ServerSettings = Field(default_factory=ServerSettings)

    WHISPER: WhisperSettings = Field(default_factory=WhisperSettings)
    EMBEDDINGS: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)
    LLM: LLMSettings = Field(default_factory=LLMSettings)

    PREFECT: PrefectSettings = Field(default_factory=PrefectSettings)
    LANGSMITH: LangsmithSettings = Field(default_factory=LangsmithSettings)

    DOWNLOADER: DownloaderSettings = Field(default_factory=DownloaderSettings)
    TRANSCRIBER: TranscriberSettings = Field(default_factory=TranscriberSettings)
    SCRAPER: ScraperSettings = Field(default_factory=ScraperSettings)

    PROMPTS: PromptsSettings = Field(default_factory=PromptsSettings)

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # API Documentation URLs
    DOCS_URL: str | None = Field(
        default="/docs",
        description="Swagger UI documentation endpoint",
    )
    REDOC_URL: str | None = Field(
        default="/redoc",
        description="ReDoc documentation endpoint",
    )
    OPENAPI_URL: str | None = Field(
        default="/openapi.json",
        description="OpenAPI JSON schema endpoint",
    )
    HEALTH_URL: str = Field(default="/health", description="Healthcheck endpoint")

    API_URL: str = Field(default="/api", description="API prefix path")
    FRONTEND_URL: HttpUrl = Field(
        default=HttpUrl("http://localhost:3000"),
        description="Frontend URL for CORS",
    )

    DOMAIN_NAME: str | None = Field(default="tu-dominio.com", description="Domain Name")
    SSL_EMAIL: EmailStr | None = Field(
        default="tu-email@example.com",
        description="Email used for SSL certificates",
    )

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
