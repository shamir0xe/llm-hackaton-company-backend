from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class MaskedChatSession(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: Optional[str] = None
