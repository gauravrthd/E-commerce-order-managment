
from decimal import Decimal

from sqlalchemy import (
    String, Text, Numeric, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    stock: Mapped[int] = mapped_column(
        nullable=False, default=0
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_product_price"),
        
        CheckConstraint("stock >= 0", name="ck_product_stock"),
    )
