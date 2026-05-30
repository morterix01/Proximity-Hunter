import hashlib

from bs4 import BeautifulSoup

from ..schemas import ScrapedItem
from .base import BaseScraper
from .util import parse_euro

UNIEURO_TARGETS = [
    "https://www.unieuro.it/online/Smartphone",
]


class UnieuroScraper(BaseScraper):
    store = "unieuro"

    def targets(self) -> list[str]:
        return UNIEURO_TARGETS

    def parse(self, html: str, url: str) -> ScrapedItem | None:
        soup = BeautifulSoup(html, "html.parser")

        # Single product page layout.
        title_el = soup.select_one("h1.product-name, h1[itemprop='name']")
        price_el = soup.select_one(".price .new-price, .product-price .price, [itemprop='price']")
        old_el = soup.select_one(".price .old-price, .product-price .strikethrough")

        if not title_el or not price_el:
            return None

        title = title_el.get_text(strip=True)
        price = parse_euro(price_el.get("content") or price_el.get_text())
        ref = parse_euro(old_el.get_text()) if old_el else None
        if price is None:
            return None

        img_el = soup.select_one("img.product-image, img[itemprop='image']")
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
        # Unieuro URLs carry a numeric pid; fall back to a stable hash.
        digits = "".join(ch for ch in url.rsplit("/", 1)[-1] if ch.isdigit())
        return digits or hashlib.sha1(title.encode()).hexdigest()[:16]
