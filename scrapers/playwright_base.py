from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from .base import Scraper

log = logging.getLogger("scraper.playwright_base")


@contextmanager
def browser_page(viewport: tuple[int, int] = (1366, 900)) -> Iterator:
    """Yield a Playwright Page in a managed Chromium context.

    Lazy imports playwright so other scrapers (and CI without browsers
    installed) keep working.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        try:
            context = browser.new_context(
                viewport={"width": viewport[0], "height": viewport[1]},
                locale="nl-NL",
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            yield page
        finally:
            browser.close()


def dismiss_cookie_banner(page) -> None:
    """Best-effort: click any obvious 'accept all' cookie button."""
    selectors = [
        "button:has-text('Accepteer alle')",
        "button:has-text('Accept all')",
        "button:has-text('Alles accepteren')",
        "button:has-text('Akkoord')",
        "button:has-text('Accept')",
        "button#cookieAccept",
        "[id*='cookie'] button",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=500):
                btn.click(timeout=1500)
                page.wait_for_timeout(400)
                return
        except Exception:
            continue


class PlaywrightScraper(Scraper):
    """Base class for SPA sites that need a real browser."""
    use_playwright = True
