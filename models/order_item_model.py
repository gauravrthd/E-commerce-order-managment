
from decimal import Decimal

from sqlalchemy import (
    ForeignKey, Numeric, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "order_id", "product_id",
            name="uq_order_item_product"
        ),
        CheckConstraint(
            "quantity > 0", name="ck_order_item_quantity"
        ),
        CheckConstraint(
            "price > 0", name="ck_order_item_price"
        ),
    )
