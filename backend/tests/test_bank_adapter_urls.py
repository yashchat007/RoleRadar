import re

from app.discovery.adapters.listing_browser import unique_matching_urls

BOFA_RE = re.compile(r"^https://careers\.bankofamerica\.com/en-us/job-detail/\d+", re.I)
JPM_RE = re.compile(
    r"^https://jpmc\.fa\.oraclecloud\.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/\d+",
    re.I,
)
MS_RE = re.compile(r"^https://morganstanley\.eightfold\.ai/careers/job/\d+", re.I)
GS_RE = re.compile(r"^https://higher\.gs\.com/roles/\d+", re.I)


def test_bofa_fixture_urls():
    hrefs = [
        "https://careers.bankofamerica.com/en-us/job-detail/26032611/slug",
        "https://boards.greenhouse.io/x/1",
    ]
    urls = unique_matching_urls(hrefs, BOFA_RE)
    assert len(urls) == 1


def test_jpm_fixture_urls():
    hrefs = [
        "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210794811/?q=1",
        "https://evil.com/job/1",
    ]
    urls = unique_matching_urls(hrefs, JPM_RE)
    assert len(urls) == 1
    assert "/job/210794811" in urls[0]


def test_ms_and_gs_fixture_urls():
    ms = unique_matching_urls(
        ["https://morganstanley.eightfold.ai/careers/job/549799037679", "https://x.com"],
        MS_RE,
    )
    gs = unique_matching_urls(["https://higher.gs.com/roles/187162", "https://higher.gs.com/campus"], GS_RE)
    assert len(ms) == 1
    assert len(gs) == 1
