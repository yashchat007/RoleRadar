import asyncio
import re

from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://stripe.com/jobs/search", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        items = await page.eval_on_selector_all(
            "a[href*='/careers/listing/']",
            """els => els.map(e => ({ href: e.href, text: (e.innerText || '').trim().slice(0,120) }))""",
        )
        uniq = {}
        for it in items:
            uniq[it["href"]] = it["text"]
        print("listings", len(uniq))
        for href, text in list(uniq.items())[:5]:
            print(href, "|", text)
        if uniq:
            url = next(iter(uniq))
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            title = await page.title()
            h1 = await page.locator("h1").first.inner_text() if await page.locator("h1").count() else ""
            print("detail title", title)
            print("h1", h1[:200])
            apply = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href).filter(h => h.includes('stripe.com'))",
            )
            print("stripe links on detail", len(apply))
        await browser.close()


asyncio.run(main())
