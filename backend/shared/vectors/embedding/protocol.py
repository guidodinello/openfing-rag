from typing import Any, Protocol

from langchain_core.embeddings import Embeddings


class EmbedderProtocol(Protocol):
    @property
    def model(self) -> Embeddings: ...

    def model_info(self) -> dict[str, Any]: ...
