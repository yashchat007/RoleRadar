"""Quick official careers probe for companies without adapters (browser)."""

import asyncio
import logging

from app.discovery.browser import browser_page
from app.discovery.adapters.listing_browser import collect_hrefs, scroll_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROBES = {
    "Netflix": "https://explore.jobs.netflix.net/careers",
    "Adobe": "https://careers.adobe.com/us/en/search-results",
    "NVIDIA": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "Salesforce": "https://careers.salesforce.com/en/jobs/",
    "Datadog": "https://careers.datadoghq.com/all-jobs/",
    "Uber": "https://www.uber.com/us/en/careers/list/",
    "Oracle": "https://careers.oracle.com/en/sites/jobsearch/jobs",
    "Cisco": "https://jobs.cisco.com/jobs/SearchJobs",
    "Qualcomm": "https://careers.qualcomm.com/careers-home/jobs",
    "Intuit": "https://jobs.intuit.com/search-jobs",
    "Goldman Sachs": "https://higher.gs.com/results",
}


async def main() -> None:
    async with browser_page() as page:
        for name, url in PROBES.items():
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=90_000)
                await page.wait_for_timeout(4000)
                await scroll_page(page, 4)
                hrefs = await collect_hrefs(page)
                hosts = sorted({h.split("/")[2] for h in hrefs if h.startswith("http")})
                logger.info("%s: %s hrefs, hosts=%s", name, len(hrefs), hosts[:8])
            except Exception as e:
                logger.warning("%s: probe failed: %s", name, e)


if __name__ == "__main__":
    asyncio.run(main())
