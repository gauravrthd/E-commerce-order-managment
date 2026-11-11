
from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    mobile: Mapped[str] = mapped_column(
        String(15), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="customer"
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('customer', 'shopkeeper', 'admin')",
            name="ck_users_role"
        ),
    )
