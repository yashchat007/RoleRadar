import httpx
import pytest

from app.discovery.http_client import discovery_http_client


@pytest.mark.asyncio
async def test_blocklisted_host_rejected():
    async with discovery_http_client() as client:
        with pytest.raises(httpx.RequestError):
            await client.get("https://boards-api.greenhouse.io/v1/boards/foo/jobs")
