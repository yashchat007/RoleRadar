from app.discovery.adapters.bofa import _card_passes_intern_india
from app.discovery.adapters.meta import _title_suggests_intern


def test_bofa_card_requires_india_and_intern_signal():
    assert _card_passes_intern_india("Summer Analyst\nLocation Mumbai, India\nPosted today")
    assert not _card_passes_intern_india("Software Engineer III\nLocation Mumbai, India")
    assert not _card_passes_intern_india("Summer Analyst\nLocation New York, NY")


def test_meta_intern_title_signal():
    assert _title_suggests_intern("Software Engineering Intern")
    assert not _title_suggests_intern("Software Engineer")
