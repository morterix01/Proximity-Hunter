import re

from bs4 import BeautifulSoup

from ..schemas import ScrapedItem
from .base import BaseScraper
from .util import parse_euro

# Replace with your real watchlist (load from DB/config in production).
AMAZON_TARGETS = [
    "https://www.amazon.it/dp/B0CHX1W1XY",
]


class AmazonScraper(BaseScraper):
    store = "amazon"

    def targets(self) -> list[str]:
        return AMAZON_TARGETS

    def parse(self, html: str, url: str) -> ScrapedItem | None:
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("#productTitle")
        title = title_el.get_text(strip=True) if title_el else None

        # BuyBox current price. Amazon splits whole/fraction; #corePrice exposes the
        # combined ".a-offscreen" string which is the most reliable.
        price = None
        for sel in (
            "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
            "#corePrice_feature_div .a-price .a-offscreen",
            "#price_inside_buybox",
            "span.a-price span.a-offscreen",
        ):
            el = soup.select_one(sel)
            if el:
                price = parse_euro(el.get_text())
                if price:
                    break

        # List / struck price -> reference baseline.
        ref = None
        ref_el = soup.select_one(
            ".basisPrice .a-offscreen, span.a-price.a-text-price span.a-offscreen"
        )
        if ref_el:
            ref = parse_euro(ref_el.get_text())

        img_el = soup.select_one("#landingImage, #imgBlkFront")
        image_url = img_el.get("src") if img_el else None

        in_stock = bool(soup.select_one("#add-to-cart-button")) or price is not None

        asin = self._asin(url)
        if not title or price is None or not asin:
            return None

        return ScrapedItem(
            store=self.store,
            external_id=asin,
            title=title,
            url=url,
            image_url=image_url,
            price=price,
            in_stock=in_stock,
            reference_price=ref,
        )

    @staticmethod
    def _asin(url: str) -> str | None:
        m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
        return m.group(1) if m else None
