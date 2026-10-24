"""Probe official Meta job detail pages (one URL at a time)."""

import asyncio
import json
import re
import sys

from app.discovery.browser import browser_page

CLOSED_PATTERNS = re.compile(
    r"no longer (available|accepting)|position (has been )?filled|job (is )?closed|"
    r"this (role|position|job) (is )?no longer|404|page not found|not found",
    re.I,
)
APPLY_PATTERNS = re.compile(r"apply now|apply for this job|submit application", re.I)


async def probe(url: str) -> dict:
    async with browser_page() as page:
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            await page.wait_for_timeout(4000)
            status = resp.status if resp else None
            final_url = page.url
            title = await page.title()
            body = (await page.inner_text("body"))[:12_000]
            h1 = ""
            if await page.locator("h1").count():
                h1 = (await page.locator("h1").first.inner_text()).strip()[:200]
            og = ""
            if await page.locator("meta[property='og:title']").count():
                og = (await page.locator("meta[property='og:title']").first.get_attribute("content")) or ""
            has_apply = bool(APPLY_PATTERNS.search(body))
            closed_hint = bool(CLOSED_PATTERNS.search(body)) or status == 404
            login_wall = "log in" in body.lower() and "password" in body.lower()
            return {
                "url": url,
                "http_status": status,
                "final_url": final_url,
                "document_title": title,
                "h1": h1,
                "og_title": og,
                "has_apply_cta": has_apply,
                "closed_hint": closed_hint,
                "login_wall": login_wall,
                "body_snippet": body[:500].replace("\n", " "),
            }
        except Exception as e:
            return {"url": url, "error": str(e)}


async def main(urls: list[str]) -> None:
    results = []
    for url in urls:
        print("Probing", url, file=sys.stderr)
        results.append(await probe(url))
        await asyncio.sleep(2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
