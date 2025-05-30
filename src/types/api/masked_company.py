from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class MaskedCompany(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data: Optional[str] = None
