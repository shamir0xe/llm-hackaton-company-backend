from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.decorated_base import DecoratedBase


class Company(DecoratedBase):
    __tablename__ = "companies"

    session_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    data: Mapped[str] = mapped_column(nullable=True)
