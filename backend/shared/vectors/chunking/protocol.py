from typing import Any, Protocol


class ChunkerProtocol(Protocol):
    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]: ...
