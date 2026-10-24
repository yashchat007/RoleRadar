import re

from app.discovery.adapters.listing_browser import unique_matching_urls
from app.discovery.normalize import canonicalize_url, source_job_key_from_url

GOOGLE_RE = re.compile(
    r"^https://www\.google\.com/about/careers/applications/jobs/results/\d+-[a-z0-9-]+",
    re.I,
)
AMAZON_RE = re.compile(r"^https://www\.amazon\.jobs/en/jobs/\d+/[a-z0-9-]+", re.I)

# Representative hrefs observed on official search pages (not fabricated job content).
GOOGLE_FIXTURE_HREFS = [
    "https://www.google.com/about/careers/applications/jobs/results/121031937400677062-senior-tpu-validation-engineer?location=United%20States",
    "https://www.google.com/about/careers/applications/jobs/results/999999999999999999-software-engineer",
    "https://boards.greenhouse.io/acme/123",
]

AMAZON_FIXTURE_HREFS = [
    "https://www.amazon.jobs/en/jobs/10386857/software-engineer",
    "https://www.amazon.jobs/en/jobs/10526510/software-development-engineer-leo-software",
    "https://jobs.lever.co/example",
]


def test_google_fixture_extracts_only_official_urls():
    urls = unique_matching_urls(GOOGLE_FIXTURE_HREFS, GOOGLE_RE)
    assert len(urls) == 2
    assert all("google.com/about/careers" in u for u in urls)
    assert canonicalize_url(urls[0]) == urls[0]


def test_amazon_fixture_rejects_third_party():
    urls = unique_matching_urls(AMAZON_FIXTURE_HREFS, AMAZON_RE)
    assert len(urls) == 2
    assert source_job_key_from_url(urls[0]) != source_job_key_from_url(urls[1])
