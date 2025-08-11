import uuid

from pydantic import UUID5

# Application namespace for deterministic UUIDs
TRANSCRIPTION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "openchat.rag")

type ChunkId = UUID5


def generate_chunk_uuid(transcription_id: int, chunk_index: int) -> ChunkId:
    """
    Generate a deterministic UUID for a transcription chunk.

    This ensures:
    - Same transcription + chunk always gets same UUID
    - Clean upserts when re-transcribing
    - Easy calculation for deletion/updates
    """
    seed = f"transcription_{transcription_id}_chunk_{chunk_index}"
    return str(uuid.uuid5(TRANSCRIPTION_NAMESPACE, seed))
