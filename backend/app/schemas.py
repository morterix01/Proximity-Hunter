from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store: str
    title: str
    url: str
    image_url: str | None
    tier: str                 # error | super | none
    old_price: float
    new_price: float
    drop_pct: float
    created_at: datetime


class SearchResultOut(BaseModel):
    """A product matched by /api/search, with its latest scraped price + tier."""

    model_config = ConfigDict(from_attributes=True)

    product_id: int
    store: str
    title: str
    url: str
    image_url: str | None = None
    price: float | None = None            # latest scraped price
    reference_price: float | None = None  # baseline the drop is measured against
    in_stock: bool | None = None
    drop_pct: float = 0.0                  # current drop vs reference
    tier: str = "none"                     # error | super | none
    last_seen: datetime | None = None      # when this price was last scraped


class WatchIn(BaseModel):
    url: str = Field(min_length=8, max_length=1024)
    store: str | None = None   # auto-detected from the URL domain when omitted
    title: str | None = None


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store: str
    url: str
    title: str | None = None
    created_at: datetime


class DeviceRegisterIn(BaseModel):
    fcm_token: str = Field(min_length=8, max_length=512)
    platform: str = "ios"


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str


class ScrapedItem(BaseModel):
    """Normalized output every scraper returns."""

    store: str
    external_id: str
    title: str
    url: str
    image_url: str | None = None
    price: float
    in_stock: bool = True
    reference_price: float | None = None   # list/struck price if the page exposes one
