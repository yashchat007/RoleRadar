import asyncio
import re

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.cloudflare.com/careers/jobs/", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        cf = set(re.findall(r"https://www\.cloudflare\.com/careers/[a-zA-Z0-9_./-]+", html))
        gh = set(re.findall(r"https://boards\.greenhouse\.io/cloudflare/jobs/\d+", html))
        print("cloudflare.com urls", len(cf))
        for u in sorted(cf)[:20]:
            print(" ", u)
        print("greenhouse urls", len(gh))
        # click first job card if any on-page
        cards = await page.query_selector_all("a[href*='cloudflare.com/careers']")
        print("cf anchor count", len(cards))
        await browser.close()


asyncio.run(main())
