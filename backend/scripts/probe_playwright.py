import asyncio
import re

from playwright.async_api import async_playwright


async def probe(name: str, url: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href).filter(h => h.includes('job') || h.includes('career'))",
        )
        print(f"\n=== {name} {page.url} links={len(links)}")
        for h in sorted(set(links))[:15]:
            print(h)
        text = await page.content()
        print("len", len(text))
        if "stripe.com" in url:
            rows = await page.query_selector_all("[data-testid], tr, article")
            print("row-like", len(rows))
        await browser.close()


async def main() -> None:
    await probe("stripe", "https://stripe.com/jobs/search")
    await probe("cloudflare", "https://www.cloudflare.com/careers/jobs/")


asyncio.run(main())
