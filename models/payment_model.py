
from decimal import Decimal

from sqlalchemy import (
    String, Numeric, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        unique=True,
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0", name="ck_payment_amount"
        ),
        CheckConstraint(
            "payment_method IN ('upi', 'card', 'cod')",
            name="ck_payment_method"
        ),
        CheckConstraint(
            "payment_status IN ('pending', 'success', 'failed')",
            name="ck_payment_status"
        ),
    )
