from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PrivacyBase(BaseModel):
    title: str
    description: str
    content: str
    effective_date: datetime

class PrivacyCreate(PrivacyBase):
    pass

class PrivacyUpdate(PrivacyBase):
    pass

class Privacy(PrivacyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 