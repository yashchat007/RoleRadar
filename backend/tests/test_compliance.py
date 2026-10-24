from app.discovery.compliance import assert_official_url, is_host_blocklisted


def test_blocklist_greenhouse_api():
    assert is_host_blocklisted("https://boards-api.greenhouse.io/v1/boards/acme/jobs")


def test_allow_official_stripe():
    assert not is_host_blocklisted("https://stripe.com/jobs/search")
    assert_official_url("https://stripe.com/jobs/123", frozenset({"stripe.com"}))
