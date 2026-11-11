
from sqlalchemy import (
    ForeignKey, Text, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )

    rating: Mapped[int] = mapped_column(
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "product_id",
            name="uq_review_user_product"
        ),
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="ck_review_rating"
        ),
    )
