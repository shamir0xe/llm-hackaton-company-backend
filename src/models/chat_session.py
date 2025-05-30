from sqlalchemy.orm import Mapped, mapped_column

from src.models.decorated_base import DecoratedBase


class ChatSession(DecoratedBase):
    __tablename__ = "chat_sessions"

    messages: Mapped[str] = mapped_column(nullable=True)
