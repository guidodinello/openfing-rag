from typing import Protocol

import requests
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class HTTPClient(Protocol):
    def get(self, url: str, **kwargs) -> requests.Response: ...


class RateLimitedHTTPClient:
    """Wrapper with rate limiting."""

    def __init__(self, session: requests.Session):
        self._session = session

    def get(self, url: str, **kwargs) -> requests.Response:
        return _rate_limited_get(self._session, url, **kwargs)


@sleep_and_retry
@limits(calls=100, period=1)
def _rate_limited_get(session: requests.Session, url: str, **kwargs) -> requests.Response:
    return session.get(url, **kwargs)


def get_http_client() -> HTTPClient:
    session = requests.Session()

    # Global Headers
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; OpenFing-Scraper/1.0)",
        },
    )

    adapter = HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        ),
        pool_connections=10,
        pool_maxsize=20,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return RateLimitedHTTPClient(session)
