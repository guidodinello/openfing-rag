from typing import Annotated

from fastapi import HTTPException, Path, Query, status

from shared.api.router import create_auth_routers
from shared.database.api.v1.schemas import ListTranscriptionsResponse, Transcription, TranscriptionResponse
from shared.database.service_dependencies import TranscriptionServiceDep
from shared.enums import WhisperModelSize

routers = create_auth_routers()


@routers.read.get(
    "/{course_code}/{lesson_number}",
    status_code=status.HTTP_200_OK,
    summary="Get transcription",
    description="Retrieve transcription for a specific course lesson",
)
async def get_transcription(
    service: TranscriptionServiceDep,
    course_code: str = Path(..., description="Course code", example="agpi"),
    lesson_number: int = Path(..., description="Lesson number", ge=1, example=1),
    model_size: Annotated[
        WhisperModelSize | None,
        Query(description="Filter by model size"),
    ] = None,
) -> TranscriptionResponse:
    result = service.get_transcription(course_code, lesson_number, model_size)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.message,
        )

    return TranscriptionResponse.success_response(
        message="Transcription retrieved successfully",
        data=Transcription.from_transcription_result(result),
    )


@routers.read.get(
    "/transcriptions",
    summary="List transcriptions",
    description="List all transcriptions with optional filtering",
)
async def list_transcriptions(
    service: TranscriptionServiceDep,
    course_code: str | None = Query(
        None,
        description="Filter by course code",
        example="agpi",
    ),
) -> ListTranscriptionsResponse:
    result = service.list_transcriptions(course_code)
    if not result.success:
        return ListTranscriptionsResponse.error_response(message=result.message)

    return ListTranscriptionsResponse.success_response(
        message="Transcriptions retrieved successfully",
        data=[Transcription.from_transcription_result(tr) for tr in result.items],
    )
