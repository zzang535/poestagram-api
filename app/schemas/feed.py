from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.file import File

class FeedBase(BaseModel):
    description: Optional[str] = None

class FeedCreate(FeedBase):
    file_ids: List[int] = []

class FeedResponse(FeedBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: List[File] = []

    class Config:
        from_attributes = True

class FeedListResponse(BaseModel):
    feeds: List[FeedResponse]
    total: int
