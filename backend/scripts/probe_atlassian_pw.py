import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://www.atlassian.com/company/careers/all-jobs",
            wait_until="domcontentloaded",
            timeout=120000,
        )
        await page.wait_for_timeout(8000)
        links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        atl = sorted({h for h in links if "atlassian.com" in h and "/careers/" in h})
        icims = sorted({h for h in links if "icims.com" in h})
        print("atlassian careers urls", len(atl))
        for h in atl[:25]:
            print(" ", h)
        print("icims", len(icims))
        await browser.close()


asyncio.run(main())
