import hashlib

from bs4 import BeautifulSoup

from ..schemas import ScrapedItem
from .base import BaseScraper
from .util import parse_euro

MEDIAWORLD_TARGETS = [
    "https://www.mediaworld.it/it/product/_smartphone.html",
]


class MediaWorldScraper(BaseScraper):
    store = "mediaworld"

    def targets(self) -> list[str]:
        return MEDIAWORLD_TARGETS

    def parse(self, html: str, url: str) -> ScrapedItem | None:
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h1[data-test='product-title'], h1.product-title")
        # MediaWorld marks the active promo price; struck price is the reference.
        price_el = soup.select_one(
            "[data-test='product-price'], .price-current, [itemprop='price']"
        )
        old_el = soup.select_one(".price-old, del, s")

        if not title_el or not price_el:
            return None

        title = title_el.get_text(strip=True)
        price = parse_euro(price_el.get("content") or price_el.get_text())
        ref = parse_euro(old_el.get_text()) if old_el else None
        if price is None:
            return None

        img_el = soup.select_one("img[data-test='product-image'], img.product-image")
        image_url = img_el.get("src") if img_el else None

        return ScrapedItem(
            store=self.store,
            external_id=self._sku(url, title),
            title=title,
            url=url,
            image_url=image_url,
            price=price,
            in_stock=True,
            reference_price=ref,
        )

    @staticmethod
    def _sku(url: str, title: str) -> str:
        slug = url.rstrip("/").rsplit("/", 1)[-1].replace(".html", "")
        return slug or hashlib.sha1(title.encode()).hexdigest()[:16]
