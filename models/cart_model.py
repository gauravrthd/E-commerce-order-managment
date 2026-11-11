
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Cart(Base):
    __tablename__ = "cart"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False, default=1
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "product_id",
            name="uq_cart_user_product"
        ),
        CheckConstraint(
            "quantity > 0", name="ck_cart_quantity"
        ),
    )
