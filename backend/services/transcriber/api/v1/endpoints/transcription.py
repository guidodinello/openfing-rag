from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from transcriber.core.processor import Processor
from transcriber.schemas.transcription import TranscriptionResponse, TranscriptionUpdateRequest

router = APIRouter()


@router.get(
    "/transcribe/{course_acronym}/{class_number}",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a transcription",
    description="Retrieve a transcription for a specific course class",
)
async def get_transcription(
    course_acronym: str,
    class_number: int,
    processor: Annotated[Processor, Depends()],
    model_size: str | None = None,
) -> TranscriptionResponse:
    is_successful, message = processor.get_transcription(
        course_acronym,
        class_number,
        model_size,
    )
    if not is_successful:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return TranscriptionResponse(message=message)


@router.put(
    "/transcribe/{course_acronym}/{class_number}",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a transcription",
    description="Create or update the transcription of a specific course class",
)
async def update_transcription(
    course_acronym: str,
    class_number: int,
    request: TranscriptionUpdateRequest,
    processor: Annotated[Processor, Depends()],
):
    is_successful, message = processor.update_transcription(
        course_acronym,
        class_number,
        request.model_size,
        request.language,
    )
    if not is_successful:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return TranscriptionResponse(message="Transcription updated successfully")
