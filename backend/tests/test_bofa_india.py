from app.discovery.adapters.bofa import _bofa_slug_indicates_india


def test_bofa_slug_india_markers():
    assert _bofa_slug_indicates_india(
        "https://careers.bankofamerica.com/en-us/job-detail/123/summer-analyst-bengaluru-india-123"
    )
    assert not _bofa_slug_indicates_india(
        "https://careers.bankofamerica.com/en-us/job-detail/456/summer-analyst-london-uk-456"
    )
