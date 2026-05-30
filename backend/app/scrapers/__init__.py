from .amazon_scraper import AmazonScraper
from .base import BaseScraper
from .mediaworld_scraper import MediaWorldScraper
from .unieuro_scraper import UnieuroScraper

SCRAPERS: list[BaseScraper] = [
    AmazonScraper(),
    UnieuroScraper(),
    MediaWorldScraper(),
]

__all__ = ["BaseScraper", "SCRAPERS"]
