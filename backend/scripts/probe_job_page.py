import asyncio
import sys

from app.discovery.browser import browser_page

URL = sys.argv[1] if len(sys.argv) > 1 else (
    "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210794811"
)


async def main() -> None:
    async with browser_page() as page:
        await page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
        await page.wait_for_timeout(6000)
        selectors = [
            "h1",
            '[data-automation-id="jobTitle"]',
            '[data-automation-id="requisitionDescription"]',
            "meta[property='og:title']",
            "title",
        ]
        for sel in selectors:
            loc = page.locator(sel)
            if sel.startswith("meta"):
                print(sel, await loc.get_attribute("content"))
            elif sel == "title":
                print("document.title", await page.title())
            else:
                print(sel, await loc.count(), (await loc.first.inner_text())[:150] if await loc.count() else "")


if __name__ == "__main__":
    asyncio.run(main())
