import asyncio
import re

from playwright.async_api import async_playwright

PROBES = [
    ("Meta", "https://www.metacareers.com/jobs"),
    ("Amazon", "https://www.amazon.jobs/en/search?base_query=software"),
    ("Apple", "https://jobs.apple.com/en-us/search"),
]


async def probe(name: str, url: str):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        try:
            await page.goto(url, timeout=90_000)
            await page.wait_for_timeout(8000)
            for _ in range(6):
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(600)
            hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            print(f"\n=== {name} ({page.url[:70]}) ===")
            patterns = [
                ("meta", "metacareers.com"),
                ("amazon", "amazon.jobs"),
                ("apple", "jobs.apple.com"),
            ]
            for label, dom in patterns:
                m = sorted({h for h in hrefs if dom in h and "/job" in h.lower() or re.search(r"/\d{5,}", h)})
                if m:
                    print(label, len(m))
                    for x in list(m)[:8]:
                        print(" ", x[:120])
        except Exception as e:
            print(name, "ERR", e)
        await b.close()


async def main():
    for n, u in PROBES:
        await probe(n, u)


if __name__ == "__main__":
    asyncio.run(main())
