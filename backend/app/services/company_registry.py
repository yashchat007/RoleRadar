"""Active company registry for scheduled discovery and Discover UI."""

ACTIVE_REGISTRY_COMPANIES: frozenset[str] = frozenset(
    {
        "Google",
        "Microsoft",
        "Amazon",
        "Bank of America",
        "JPMorgan Chase",
        "Morgan Stanley",
        "Goldman Sachs",
        "Meta",
    }
)

# Official career entry points (audit reference).
CAREER_URLS: dict[str, str] = {
    "Google": "https://www.google.com/about/careers/applications/",
    "Microsoft": "https://careers.microsoft.com/",
    "Amazon": "https://www.amazon.jobs/",
    "Meta": "https://www.metacareers.com/",
    "Goldman Sachs": "https://higher.gs.com/results",
    "Bank of America": "https://careers.bankofamerica.com/",
    "JPMorgan Chase": "https://www.jpmorganchase.com/careers/explore-opportunities",
    "Morgan Stanley": "https://www.morganstanley.com/careers/career-opportunities-search/",
}
