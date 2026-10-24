from app.matching.eligibility_display import derive_eligibility_label, eligibility_label_text
from app.services.company_brand import career_page_domain, company_logo_url
from app.services.company_priority import discover_company_sort_key, technical_priority_rank


def test_technical_employers_sort_before_others():
    names = ["Walmart Global Tech", "Google", "Bank of America", "Microsoft"]
    names.sort(key=discover_company_sort_key)
    assert names[0] == "Google"
    assert names[1] == "Microsoft"
    assert names.index("Walmart Global Tech") > names.index("Microsoft")


def test_priority_rank_only_for_listed_tech():
    assert technical_priority_rank("Stripe") == 11
    assert technical_priority_rank("JPMorgan Chase") is None


def test_logo_url_uses_careers_domain():
    url = company_logo_url("https://stripe.com/jobs/search")
    assert url is not None
    assert "stripe.com" in url
    assert career_page_domain("https://www.atlassian.com/company/careers") == "atlassian.com"


def test_eligibility_labels():
    label, _ = derive_eligibility_label(
        has_match=True,
        has_resume=True,
        hard_eligible=False,
        eligibility_reasons=["Posting states visa sponsorship is not available"],
        requirements=[],
    )
    assert eligibility_label_text(label) == "Potential eligibility issue"

    label2, _ = derive_eligibility_label(
        has_match=True,
        has_resume=True,
        hard_eligible=True,
        eligibility_reasons=[],
        requirements=[{"text": "Python", "status": "unclear"}],
    )
    assert eligibility_label_text(label2) == "Eligibility unclear"

    label3, _ = derive_eligibility_label(
        has_match=True,
        has_resume=True,
        hard_eligible=True,
        eligibility_reasons=[],
        requirements=[{"text": "Python", "status": "met"}],
    )
    assert eligibility_label_text(label3) == "Eligible"


def test_hide_ineligible_only_hard_block():
    """Document: hide filter must use hard_eligible=False, not low score."""
    label, _ = derive_eligibility_label(
        has_match=True,
        has_resume=True,
        hard_eligible=True,
        eligibility_reasons=[],
        requirements=[{"text": "x", "status": "unclear"}],
    )
    assert label != "issue"
