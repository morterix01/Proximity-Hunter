import asyncio
import logging
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright

from ..schemas import ScrapedItem
from .proxy import proxy_for_playwright, random_user_agent

log = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Headless-browser scraper. Subclass per store.

    Subclass contract:
      - store: unique store key ("amazon", ...)
      - targets(): the product URLs to watch
      - parse(html, url): turn one product page into a ScrapedItem (or None)
    """

    store: str = "base"
    nav_timeout_ms: int = 30_000
    polite_delay_s: float = 1.5  # between pages, reduce footprint / rate-limit risk

    @abstractmethod
    def targets(self) -> list[str]:
        ...

    @abstractmethod
    def parse(self, html: str, url: str) -> ScrapedItem | None:
        ...

    async def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        proxy = proxy_for_playwright()

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, proxy=proxy)
            try:
                for url in self.targets():
                    context = await browser.new_context(
                        user_agent=random_user_agent(),
                        locale="it-IT",
                        viewport={"width": 1366, "height": 900},
                    )
                    page = await context.new_page()
                    try:
                        await page.goto(url, timeout=self.nav_timeout_ms, wait_until="domcontentloaded")
                        html = await page.content()
                        item = self.parse(html, url)
                        if item:
                            items.append(item)
                    except Exception as exc:  # one bad page must not kill the batch
                        log.warning("[%s] failed %s: %s", self.store, url, exc)
                    finally:
                        await context.close()
                    await asyncio.sleep(self.polite_delay_s)
            finally:
                await browser.close()
        return items
