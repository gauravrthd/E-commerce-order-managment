
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Text, Numeric, ForeignKey,
    DateTime, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    shipping_address: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    order_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_order_total"
        ),
        CheckConstraint(
            "order_status IN "
            "('pending', 'confirmed', 'shipped', "
            "'delivered', 'cancelled')",
            name="ck_order_status"
        ),
    )
