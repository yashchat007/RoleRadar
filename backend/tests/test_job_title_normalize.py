from app.discovery.job_title import normalize_job_title
from app.discovery.normalize import requisition_id_from_url


def test_strip_google_numeric_prefix():
    url = "https://www.google.com/about/careers/applications/jobs/results/109375266236572358-slug"
    raw = "109375266236572358 Silicon Engineering Intern PhD Summer 2027"
    title, req = normalize_job_title(raw, url)
    assert req == requisition_id_from_url(url)
    assert not title.startswith("1093752")
    assert "Silicon Engineering" in title


def test_idempotent_normalize():
    url = "https://www.google.com/about/careers/applications/jobs/results/109375266236572358-slug"
    once, _ = normalize_job_title("109375266236572358 Foo Intern", url)
    twice, _ = normalize_job_title(once, url)
    assert once == twice
