
from sqlalchemy import (
    String, Text, ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Cancellation(Base):
    __tablename__ = "cancellations"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        unique=True,
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    cancellation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    __table_args__ = (
        CheckConstraint(
            "cancellation_status IN "
            "('pending', 'approved', 'rejected')",
            name="ck_cancellation_status"
        ),
    )
