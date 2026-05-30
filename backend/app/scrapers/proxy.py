import itertools
import random

from ..config import settings

# Small rotating pool. In production back this with a real provider (ScraperAPI,
# Bright Data, ...) or a maintained proxy list loaded from env/secret store.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

_ua_cycle = itertools.cycle(USER_AGENTS)


def next_user_agent() -> str:
    return next(_ua_cycle)


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def proxy_for_playwright() -> dict | None:
    """Return Playwright proxy config, or None when proxying disabled.

    With ScraperAPI you typically route through their proxy endpoint:
      http://scraperapi:<API_KEY>@proxy-server.scraperapi.com:8001
    """
    if not settings.use_proxy or not settings.scraper_api_key:
        return None
    return {
        "server": "http://proxy-server.scraperapi.com:8001",
        "username": "scraperapi",
        "password": settings.scraper_api_key,
    }
