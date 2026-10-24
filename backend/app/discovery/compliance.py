from urllib.parse import urlparse

from app.config import settings


def is_host_blocklisted(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return any(host == blocked or host.endswith("." + blocked) for blocked in settings.discovery_blocklist_hosts)


def assert_official_url(url: str, allowed_hosts: frozenset[str]) -> None:
    if is_host_blocklisted(url):
        raise ValueError(f"Blocked job source host: {url}")
    host = urlparse(url).hostname or ""
    if not any(host == h or host.endswith("." + h) for h in allowed_hosts):
        raise ValueError(f"URL host not allowlisted for company: {url}")
