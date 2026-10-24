import re

import httpx

SITES = [
    ("cloudflare", "https://www.cloudflare.com/careers/jobs/"),
    ("stripe", "https://stripe.com/jobs/search"),
    ("atlassian", "https://www.atlassian.com/company/careers/all-jobs"),
]

for name, url in SITES:
    try:
        r = httpx.get(
            url,
            follow_redirects=True,
            timeout=30,
            headers={"User-Agent": "RoleRadarDiscovery/0.1"},
        )
        text = r.text
        print(f"\n=== {name} {r.status_code} len={len(text)} final={r.url}")
        hosts = set(re.findall(r"https?://([a-zA-Z0-9.-]+)/", text))
        print("hosts sample", sorted(hosts)[:15])
        for pat in ["JobPosting", "jobPostings", "greenhouse", "lever.co", "ashby"]:
            print(f"  {pat}: {pat.lower() in text.lower()}")
    except Exception as e:
        print(name, "ERR", e)
