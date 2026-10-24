import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://stripe.com/jobs/search", wait_until="domcontentloaded", timeout=60000)
        for _ in range(10):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(800)
        count = await page.locator("a[href*='/careers/listing/']").count()
        print("after scroll", count)
        await browser.close()


asyncio.run(main())
