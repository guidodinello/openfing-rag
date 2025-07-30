from fastapi import status

from services.transcriber.api.v1.schemas import TranscribeRequest
from shared.api.router import AuthRouters
from shared.database.api.v1.schemas import TranscriptionFile, TranscriptionFileResponse
from shared.database.service_dependencies import TranscriptionServiceDep

routers = AuthRouters.create()


@routers.api_key.write.post(
    "/transcribe",
    status_code=status.HTTP_201_CREATED,
    summary="Transcribe a Lesson",
    description="Create or update transcription for a specific course lesson",
)
async def create_transcription(
    request: TranscribeRequest,
    service: TranscriptionServiceDep,
) -> TranscriptionFileResponse:
    result = service.transcribe_lesson(
        course_code=request.course_code,
        lesson_number=request.lesson_number,
        model_size=request.model_size,
        language=request.language,
    )

    if not result.success:
        return TranscriptionFileResponse.error_response(message=result.message)

    return TranscriptionFileResponse.success_response(
        message=result.message,
        data=TranscriptionFile.from_transcription_file_result(result),
    )
