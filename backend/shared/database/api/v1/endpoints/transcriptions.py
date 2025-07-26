from typing import Annotated

from fastapi import HTTPException, Path, Query, status

from shared.api.router import AuthRouters
from shared.database.api.v1.schemas import ListTranscriptionsResponse, Transcription, TranscriptionResponse
from shared.database.service_dependencies import TranscriptionServiceDep
from shared.enums import WhisperModelSize

routers = AuthRouters.create()


@routers.mixed.api_key_or_jwt_read.get(
    "/courses/{course_code}/lessons/{lesson_number}",
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

    print("RESULT", result)
    return TranscriptionResponse.success_response(
        message="Transcription retrieved successfully",
        data=Transcription.from_transcription_result(result),
    )


@routers.mixed.api_key_or_jwt_read.get(
    "/transcriptions",
    status_code=status.HTTP_200_OK,
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
        data=[Transcription.from_schema(tr) for tr in result.items],
    )
