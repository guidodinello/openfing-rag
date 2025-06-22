import importlib.metadata
import time
from typing import Any

import langchain_huggingface
from langchain_core.embeddings import Embeddings

from shared.config.config import get_settings
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Embedder:
    _models_cache: dict[str, Embeddings] = {}

    def __init__(
        self,
        model_name: str = settings.EMBEDDINGS.MODEL,
    ):
        self.model_name = model_name

    @property
    def model(self) -> Embeddings:
        return self._get_embeddings_model(self.model_name)

    @classmethod
    def _get_embeddings_model(cls, model_name: str) -> Embeddings:
        cache_key = f"{model_name}_{settings.EMBEDDINGS.DEVICE}"

        if cache_key not in cls._models_cache:
            cache_folder = settings.EMBEDDINGS.CACHE_DIR
            if cache_folder:
                cache_folder.mkdir(exist_ok=True, parents=True)

            logger.debug(f"Loading Embeddings {model_name=} on {settings.EMBEDDINGS.DEVICE}")
            cls._models_cache[cache_key] = langchain_huggingface.HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": settings.EMBEDDINGS.DEVICE},
                cache_folder=str(cache_folder),
                encode_kwargs=cls._model_custom_config(),
            )

        return cls._models_cache[cache_key]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        logger.info(f"Embedding {len(texts)} texts with model {self.model_name}")

        try:
            model = self._get_embeddings_model(self.model_name)

            start_time = time.time()
            embeddings = model.embed_documents(texts)
            processing_time = time.time() - start_time

            logger.debug(f"Embeddings completed in {processing_time:.2f} seconds")
            return embeddings
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    def embed_query(self, query: str) -> list[float]:
        try:
            return self._get_embeddings_model(self.model_name).embed_query(query)
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise

    @classmethod
    def _model_custom_config(cls) -> dict[str, Any]:
        return {"normalize_embeddings": True}

    def _model_info(self) -> dict[str, Any]:
        package_name = getattr(langchain_huggingface, "__name__", "unknown")
        return {
            "package": {
                "name": package_name,
                "version": importlib.metadata.version(package_name),
            },
            "model": {
                "name": self.model_name,
                "config": self._model_custom_config(),
            },
        }
