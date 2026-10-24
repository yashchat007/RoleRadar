from urllib.parse import urlparse


def career_page_domain(career_page_url: str) -> str | None:
    if not career_page_url:
        return None
    host = urlparse(career_page_url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def company_logo_url(career_page_url: str) -> str | None:
    """Favicon for the official careers site domain (no third-party logo CDN)."""
    domain = career_page_domain(career_page_url)
    if not domain:
        return None
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
