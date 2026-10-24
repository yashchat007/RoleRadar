from app.discovery.normalize import requisition_id_from_url, source_job_key_from_url


def test_google_requisition_stable_key():
    a = "https://www.google.com/about/careers/applications/jobs/results/12345-slug?x=1"
    b = "https://www.google.com/about/careers/applications/jobs/results/12345-slug"
    assert requisition_id_from_url(a) == "12345"
    assert source_job_key_from_url(a) == source_job_key_from_url(b)


def test_bofa_requisition_key():
    url = "https://careers.bankofamerica.com/en-us/job-detail/26032611/foo-bar"
    assert requisition_id_from_url(url) == "26032611"
    k1 = source_job_key_from_url(url)
    k2 = source_job_key_from_url(url + "?ref=1")
    assert k1 == k2


def test_jpm_oracle_job_id():
    url = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210794811"
    assert requisition_id_from_url(url) == "210794811"
