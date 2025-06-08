from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from shared.database.service_dependencies import TranscriptionServiceDep
from transcriber.schemas.api import TranscriptionCreateRequest, TranscriptionListResponse, TranscriptionResponse
from transcriber.schemas.enums import WhisperModelSize

router = APIRouter()


@router.get(
    "/transcribe/{course_code}/{lesson_number}",
    status_code=status.HTTP_200_OK,
    summary="Get transcription",
    description="Retrieve transcription for a specific course lesson",
)
async def get_transcription(
    service: TranscriptionServiceDep,
    course_code: str = Path(..., description="Course code", example="agpi"),
    lesson_number: int = Path(..., description="Lesson number", ge=1, example=1),
    model_size: Annotated[WhisperModelSize | None, Query(description="Filter by model size")] = None,
) -> TranscriptionResponse:
    result = service.get_transcription(course_code, lesson_number, model_size)

    if not result.success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.message)

    return result.to_api_response()


@router.post(
    "/transcribe/{course_code}/{lesson_number}",
    status_code=status.HTTP_201_CREATED,
    summary="Create transcription",
    description="Create or update transcription for a specific course lesson",
)
async def create_transcription(
    request: TranscriptionCreateRequest,
    service: TranscriptionServiceDep,
    course_code: str = Path(..., description="Course code", example="AGPI"),
    lesson_number: int = Path(..., description="Lesson number", ge=1, example=1),
) -> TranscriptionResponse:
    result = service.transcribe_lesson(
        course_code=course_code,
        lesson_number=lesson_number,
        model_size=request.model_size,
        language=request.language,
        force_retranscribe=request.force_retranscribe,
        force_revectorize=request.force_revectorize,
    )

    if not result.success:
        if "not found" in result.message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "failed to transcribe" in result.message.lower():
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(status_code=status_code, detail=result.message)

    return result.to_api_response()


@router.get(
    "/transcriptions",
    summary="List transcriptions",
    description="List all transcriptions with optional filtering",
)
async def list_transcriptions(
    service: TranscriptionServiceDep,
    course_code: str | None = Query(None, description="Filter by course code", example="agpi"),
    unvectorized_only: bool = Query(False, description="Only show unvectorized transcriptions"),
) -> TranscriptionListResponse:
    result = service.list_transcriptions(course_code, unvectorized_only)

    if not result.success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)

    return result.to_api_response()


@router.post(
    "/transcriptions/{transcription_id}/vectorize",
    summary="Vectorize transcription",
    description="Add transcription to vector store for RAG",
)
async def vectorize_transcription(
    service: TranscriptionServiceDep,
    transcription_id: int = Path(..., description="Transcription ID", ge=1),
) -> TranscriptionResponse:
    result = service.vectorize_transcription(transcription_id)

    if not result.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)

    return result.to_api_response()
