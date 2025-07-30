from fastapi import HTTPException, status

from services.scraper.api.v1.schemas import Sync, SyncResponse
from shared.api.router import AuthRouters
from shared.database.service_dependencies import ScrapingServiceDep

routers = AuthRouters.create()


@routers.api_key.admin.post(
    "/sync-all",
    status_code=status.HTTP_200_OK,
    summary="Sync all OpenFing data",
    description="Scrape all courses and lessons from OpenFing and sync to database",
)
async def sync_all_data(service: ScrapingServiceDep) -> SyncResponse:
    try:
        result = service.sync_openfing_data()
        if not result.success:
            return SyncResponse.error_response(message=result.message)

        return SyncResponse.success_response(message="Synced successully", data=Sync.from_sync_result(result))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        ) from e


@routers.api_key.write.post(
    "/sync-course/{course_code}",
    status_code=status.HTTP_200_OK,
    summary="Sync specific course",
    description="Scrape a specific course and its lessons from OpenFing",
)
async def sync_course(
    course_code: str,
    service: ScrapingServiceDep,
) -> SyncResponse:
    try:
        result = service.sync_course_only(course_code)
        if not result.success:
            return SyncResponse.error_response(message=result.message)

        return SyncResponse.success_response(
            message=f"Course '{course_code}' synced successully",
            data=Sync.from_sync_result(result),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course sync failed: {str(e)}",
        ) from e
