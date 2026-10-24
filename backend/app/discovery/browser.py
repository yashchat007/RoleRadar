from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from playwright.async_api import Browser, Page, async_playwright

from app.config import settings


@asynccontextmanager
async def browser_page() -> AsyncIterator[Page]:
    async with async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=settings.discovery_user_agent)
        try:
            yield page
        finally:
            await browser.close()
