from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.config import settings
from app.discovery.compliance import is_host_blocklisted

DEFAULT_USER_AGENT = "RoleRadarDiscovery/0.1 (+official-careers-only)"


def _enforce_allowed_request(request: httpx.Request) -> None:
    if is_host_blocklisted(str(request.url)):
        raise httpx.RequestError(
            f"Blocked discovery request to disallowed host: {request.url.host}",
            request=request,
        )


@asynccontextmanager
async def discovery_http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(45.0),
        headers={"User-Agent": settings.discovery_user_agent},
        event_hooks={"request": [_enforce_allowed_request]},
    ) as client:
        yield client
