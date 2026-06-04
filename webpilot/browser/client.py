from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import Browser, Page, sync_playwright


@contextmanager
def browser_page(headless: bool = True) -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()

