import hashlib
import re
from urllib.parse import urlparse, urlunparse

from app.discovery.compliance import assert_official_url
from app.discovery.types import NormalizedJob


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = re.sub(r"/+$", "", parsed.path) or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", parsed.query, ""))


_REQUISITION_ID = re.compile(
    r"(?:"
    r"google\.com/about/careers/applications/jobs/results/(\d+)"
    r"|apply\.careers\.microsoft\.com/careers/job/(\d+)"
    r"|amazon\.jobs/en/jobs/(\d+)"
    r"|metacareers\.com/profile/job_details/(\d+)"
    r"|careers\.bankofamerica\.com/en-us/job-detail/(\d+)"
    r"|/sites/CX_1001/job/(\d+)"
    r"|eightfold\.ai/careers/job/(\d+)"
    r"|higher\.gs\.com/roles/(\d+)"
    r")",
    re.I,
)


def requisition_id_from_url(url: str) -> str | None:
    m = _REQUISITION_ID.search(url)
    if not m:
        return None
    for g in m.groups():
        if g:
            return g
    return None


def source_job_key_from_url(url: str) -> str:
    req = requisition_id_from_url(url)
    if req:
        path = url.split("?")[0].lower()
        host = urlparse(path).netloc.replace("www.", "")
        return hashlib.sha256(f"{host}:req:{req}".encode()).hexdigest()[:32]
    path = url.split("?")[0].rstrip("/")
    return hashlib.sha256(path.lower().encode("utf-8")).hexdigest()[:32]


def content_hash(title: str, location: str | None, description: dict) -> str:
    blob = f"{title}\n{location or ''}\n{description!s}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_job_urls(job: NormalizedJob, allowed_hosts: frozenset[str]) -> None:
    assert_official_url(job.listing_url, allowed_hosts)
    assert_official_url(job.apply_url, allowed_hosts)
