import re

_PRICE_RE = re.compile(r"(\d{1,3}(?:[.\s]\d{3})*|\d+)(?:,(\d{1,2}))?")


def parse_euro(text: str | None) -> float | None:
    """Parse an Italian-formatted price string ('1.299,00 €') into a float.

    Handles thousands '.'/space separators and ',' decimal. Returns None if no
    number is found.
    """
    if not text:
        return None
    cleaned = text.replace("\xa0", " ").strip()
    m = _PRICE_RE.search(cleaned)
    if not m:
        return None
    integer = re.sub(r"[.\s]", "", m.group(1))
    decimals = m.group(2) or "0"
    try:
        return float(f"{integer}.{decimals}")
    except ValueError:
        return None
