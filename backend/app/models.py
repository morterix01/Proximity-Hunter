from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GlitchTier(str, Enum):
    ERROR = "error"      # Errore Prezzo
    SUPER = "super"      # Super Sconto
    NONE = "none"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    store: Mapped[str] = mapped_column(String(32), index=True)        # amazon | unieuro | mediaworld
    external_id: Mapped[str] = mapped_column(String(128))            # ASIN / SKU
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024))
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    reference_price: Mapped[float | None] = mapped_column(Float, nullable=True)  # baseline / list price
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    prices: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    deals: Mapped[list["Deal"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("store", "external_id", name="uq_store_external"),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(Float)
    in_stock: Mapped[bool] = mapped_column(default=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    product: Mapped["Product"] = relationship(back_populates="prices")

    __table_args__ = (Index("ix_price_product_time", "product_id", "scraped_at"),)


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    tier: Mapped[str] = mapped_column(String(16), index=True)        # GlitchTier value
    old_price: Mapped[float] = mapped_column(Float)
    new_price: Mapped[float] = mapped_column(Float)
    drop_pct: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(default=True, index=True)
    notified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    product: Mapped["Product"] = relationship(back_populates="deals")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    fcm_token: Mapped[str] = mapped_column(String(512), unique=True)
    platform: Mapped[str] = mapped_column(String(16), default="ios")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
