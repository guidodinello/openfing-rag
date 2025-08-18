import json
import uuid

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext, build_auth_context, get_client_ip

logger = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next: CallNext) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        f"Request {request_id} started: {
            json.dumps(
                {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': str(request.query_params) if request.query_params else None,
                    'client_ip': get_client_ip(request),
                    'user_agent': request.headers.get(CustomHeaders.USER_AGENT),
                    **build_auth_context(request),
                },
                default=str,
            )
        }",
    )

    response = await call_next(request)

    logger.info(
        f"Request {request_id} completed: {
            json.dumps(
                {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                },
                default=str,
            )
        }",
    )

    response.headers[CustomHeaders.REQUEST_ID] = request_id
    return response
