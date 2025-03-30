from functools import lru_cache
from pathlib import Path

import torch
from app.core.config import get_settings
from app.utils.logger import get_logger
from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingsService:
    """Service for managing embeddings generation with optimized performance."""

    def __init__(
        self,
        model_name: str,
        cache_dir: None | Path = None,
        device: None | str = None,
    ):
        self.model_name = model_name
        self.cache_dir = (
            cache_dir or Path.home() / ".cache" / "torch" / "sentence_transformers"
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize model with optimizations
        self.model = self._initialize_model()
        logger.info(
            f"Initialized {model_name} on {self.device} "
            f"(torch dtype: {self.model.device.type})"
        )

    def _initialize_model(self) -> SentenceTransformer:
        """Initialize the model with optimized settings."""
        model = SentenceTransformer(
            self.model_name,
            cache_folder=str(self.cache_dir),
            device=self.device,
            model_kwargs={
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32
            },
        )

        # If using GPU, enable additional optimizations
        if self.device == "cuda":
            model.half()  # Convert to FP16 for faster inference
            # Enable CUDA optimizations if available
            if hasattr(torch.backends, "cudnn"):
                torch.backends.cudnn.benchmark = True

        return model

    def get_batch_embeddings(
        self,
        texts: list[str],
        normalize: bool = True,
        batch_size: None | int = None,
    ) -> list[list[float]]:
        """
        Get embeddings for a batch of texts using the optimized model.

        Args:
            texts: list of input texts to embed
            normalize: Whether to L2-normalize the embeddings
            batch_size: Optional batch size override (defaults to settings)

        Returns:
            list of embedding vectors
        """
        with torch.no_grad():  # Disable gradient calculation for inference
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                convert_to_tensor=True,
                show_progress_bar=False,
                batch_size=batch_size or settings.EMBEDDINGS.BATCH_SIZE,
            )
            return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embeddings_service() -> EmbeddingsService:
    """Get or create a singleton instance of EmbeddingsService."""
    return EmbeddingsService(
        model_name=settings.EMBEDDINGS.MODEL,
        cache_dir=Path(settings.EMBEDDINGS.CACHE_DIR)
        if settings.EMBEDDINGS.CACHE_DIR
        else None,
    )
