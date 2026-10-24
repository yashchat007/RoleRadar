import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    url = "https://www.atlassian.com/company/careers/details/22983"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_timeout(5000)
        h1 = await page.locator("h1").first.inner_text() if await page.locator("h1").count() else ""
        print("h1", h1)
        loc = await page.locator("[data-testid='job-location'], .job-location").first.inner_text() if await page.locator("[data-testid='job-location']").count() else "n/a"
        print("loc try", loc)
        await browser.close()


asyncio.run(main())
