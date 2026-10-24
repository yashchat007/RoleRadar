import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    seen: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        def on_response(resp) -> None:
            url = resp.url
            if "cloudflare.com" in url and ("job" in url.lower() or "career" in url.lower() or "position" in url.lower()):
                seen.append(f"{resp.status} {url}")

        page.on("response", on_response)
        await page.goto("https://www.cloudflare.com/careers/jobs/", wait_until="networkidle", timeout=90000)
        await page.wait_for_timeout(5000)
        await browser.close()

    for line in sorted(set(seen)):
        print(line)
    print("total", len(set(seen)))


asyncio.run(main())
