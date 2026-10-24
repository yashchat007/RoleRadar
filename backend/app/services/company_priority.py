"""Display order for Discover company cards — technical employers first."""

TECH_EMPLOYER_PRIORITY: tuple[str, ...] = (
    "Google",
    "Microsoft",
    "Meta",
    "NVIDIA",
    "Adobe",
    "Qualcomm",
    "Apple",
    "Amazon",
    "Netflix",
    "Salesforce",
    "Atlassian",
    "Stripe",
    "Datadog",
    "Cloudflare",
    "Oracle",
    "Cisco",
    "Uber",
    "Dell Technologies",
)

_PRIORITY_INDEX = {name: idx for idx, name in enumerate(TECH_EMPLOYER_PRIORITY)}


def technical_priority_rank(name: str) -> int | None:
    return _PRIORITY_INDEX.get(name)


def discover_company_sort_key(name: str) -> tuple[int, int, str]:
    """Sort key: prioritized technical employers first, then alphabetical."""
    if name in _PRIORITY_INDEX:
        return (0, _PRIORITY_INDEX[name], name)
    return (1, 999, name)
