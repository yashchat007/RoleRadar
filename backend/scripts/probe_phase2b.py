"""One-off live probe for Phase 2B (Meta, BofA, JPM). Not part of pytest."""
import asyncio
import re
import sys

from app.discovery.browser import browser_page
from app.discovery.playwright_retry import goto_with_retry


async def probe_url(page, label: str, url: str, listing_re: re.Pattern[str], wait_ms: int = 8000):
    await goto_with_retry(page, url, label=label)
    await page.wait_for_timeout(wait_ms)
    hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    matches = [h for h in hrefs if listing_re.search(h.split("?")[0])]
    uniq = list(dict.fromkeys(matches))
    body = await page.inner_text("body")
    items = re.search(r"(\d+)\s+Items?", body, re.I)
    jobs = re.search(r"(\d+)\s+jobs?", body, re.I)
    print(f"\n=== {label} ===")
    print(f"URL: {url}")
    print(f"Items text: {items.group(0) if items else 'n/a'} | jobs text: {jobs.group(0) if jobs else 'n/a'}")
    print(f"Matching listing URLs: {len(uniq)}")
    for u in uniq[:8]:
        print(f"  {u}")
    return uniq


async def meta_office_probe(page):
    from app.discovery.location_extract import extract_location_from_detail_page

    for office in ("Bangalore", "Bengaluru", "Gurgaon", "Gurugram", "Hyderabad"):
        url = f"https://www.metacareers.com/jobsearch?q=intern&offices[0]={office}"
        await goto_with_retry(page, url, label=office)
        await page.wait_for_timeout(8000)
        body = await page.inner_text("body")
        m = re.search(r"(\d+)\s+Items", body)
        print(f"office={office} -> {m.group(0) if m else 'no Items line'}")
    await goto_with_retry(page, "https://www.metacareers.com/jobsearch?q=intern", label="global-intern")
    await page.wait_for_timeout(8000)
    hrefs = await page.eval_on_selector_all(
        'a[href*="job_details"]', "els => els.map(e => e.href)"
    )
    hrefs = list(dict.fromkeys(hrefs))[:8]
    print(f"global intern job_details on first screen: {len(hrefs)}")
    for h in hrefs:
        facts = await extract_location_from_detail_page(page, h, "meta_official")
        print(
            f"  {h.split('/')[-2]}: loc={facts.normalized_location!r} "
            f"india={facts.india_eligible} countries={facts.countries}"
        )


async def bofa_extra_probe(page):
    for url in (
        "https://careers.bankofamerica.com/en-us/students",
        "https://careers.bankofamerica.com/en-us/job-search?keywords=summer%20analyst&locationsearch=Bengaluru",
        "https://careers.bankofamerica.com/en-us/job-search?keywords=intern&locationsearch=Bengaluru",
    ):
        await goto_with_retry(page, url, label="bofa-extra")
        await page.wait_for_timeout(9000)
        hrefs = await page.eval_on_selector_all(
            'a[href*="job-detail"]', "els => els.map(e => e.href)"
        )
        hrefs = list(dict.fromkeys(hrefs))
        print(f"\nBofA extra {url}\n  links={len(hrefs)}")
        for h in hrefs[:6]:
            print(f"  {h}")


async def main():
    targets = sys.argv[1:] or ["meta", "bofa", "jpm"]
    async with browser_page() as page:
        if "meta" in targets:
            meta_re = re.compile(r"metacareers\.com/(?:profile/job_details|jobs)/\d+", re.I)
            for url in (
                "https://www.metacareers.com/jobsearch?q=intern&offices[0]=Bangalore",
                "https://www.metacareers.com/jobsearch?q=internship&offices[0]=Gurgaon",
                "https://www.metacareers.com/jobsearch?q=software%20engineering%20intern&offices[0]=Bangalore",
                "https://www.metacareers.com/careerprograms/students",
            ):
                await probe_url(page, "Meta", url, meta_re, 10000)
        if "bofa" in targets:
            bofa_re = re.compile(r"careers\.bankofamerica\.com/en-us/job-detail/\d+", re.I)
            for url in (
                "https://careers.bankofamerica.com/en-us/job-search/india",
                "https://careers.bankofamerica.com/en-us/job-search/india?keywords=intern",
                "https://careers.bankofamerica.com/en-us/job-search?keywords=intern&locationsearch=India",
            ):
                urls = await probe_url(page, "BofA", url, bofa_re, 7000)
                india_slug = [u for u in urls if re.search(r"india|bengaluru|mumbai|hyderabad|gurugram|chennai", u, re.I)]
                print(f"  URLs with India-ish slug: {len(india_slug)}")
        if "meta-offices" in targets:
            await meta_office_probe(page)
        if "bofa-extra" in targets:
            await bofa_extra_probe(page)
        if "jpm" in targets:
            jpm_re = re.compile(r"jpmc\.fa\.oraclecloud\.com/.*/job/\d+", re.I)
            for url in (
                "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?"
                "keyword=intern&location=India&locationId=300000000289360&locationLevel=country&mode=location",
                "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?"
                "keyword=intern&location=India",
            ):
                await probe_url(page, "JPM", url, jpm_re, 12000)


if __name__ == "__main__":
    asyncio.run(main())
