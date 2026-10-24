from app.discovery.adapters.bofa import _bofa_slug_indicates_india


def test_bofa_slug_india_marker():
    assert _bofa_slug_indicates_india(
        "https://careers.bankofamerica.com/en-us/job-detail/1/foo-bengaluru-karnataka-india-esomprank-x"
    )
    assert not _bofa_slug_indicates_india(
        "https://careers.bankofamerica.com/en-us/job-detail/1/foo-dallas-texas-united-states-esomprank-x"
    )
