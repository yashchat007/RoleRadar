import json
import re

import httpx
from bs4 import BeautifulSoup

r = httpx.get(
    "https://www.cloudflare.com/careers/jobs/",
    follow_redirects=True,
    timeout=30,
    headers={"User-Agent": "RoleRadarDiscovery/0.1"},
)
soup = BeautifulSoup(r.text, "html.parser")
for script in soup.find_all("script", type="application/ld+json"):
    data = json.loads(script.string)
    print("ld+json", type(data), str(data)[:800])

urls = set(re.findall(r"https://www\.cloudflare\.com/careers/[a-zA-Z0-9_./-]+", r.text))
print("urls", len(urls))
for u in sorted(urls)[:20]:
    print(u)
