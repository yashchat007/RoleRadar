from app.discovery.normalize import canonicalize_url, source_job_key_from_url


def test_canonicalize_strips_trailing_slash():
    assert canonicalize_url("https://stripe.com/careers/listing/foo/1/") == canonicalize_url(
        "https://stripe.com/careers/listing/foo/1"
    )


def test_source_job_key_stable():
    url = "https://stripe.com/careers/listing/ai-engineer/8144196"
    assert source_job_key_from_url(url) == source_job_key_from_url(url)
