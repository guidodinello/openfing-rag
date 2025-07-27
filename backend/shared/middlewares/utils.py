from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from shared.enums import CustomHeaders


def get_client_ip(request: Request) -> str:
    """Extract real client IP considering proxies."""
    if forwarded_for := request.headers.get(CustomHeaders.FORWARDED_FOR):
        return forwarded_for.split(",")[0].strip()
    if real_ip := request.headers.get(CustomHeaders.REAL_IP):
        return real_ip
    return request.client.host if request.client else "unknown"


CallNext = Callable[[Request], Awaitable[Response]]
