from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.schemas.file import File
from app.schemas.user import UserForFeed

# 사용자 입력용 기본 스키마
class FeedBase(BaseModel):
    description: Optional[str] = None
    frame_ratio: float = Field(ge=0.54, le=1.25, default=1.0)

# 피드 응답 스키마
class FeedResponse(FeedBase):
    id: int
    user: UserForFeed
    created_at: datetime
    updated_at: Optional[datetime] = None
    files: List[File] = []
    likes_count: int = 0

    # SQLAlchemy ORM 객체를 바로 Pydantic 모델로 변환할 수 있게 해주는 설정
    model_config = {"from_attributes": True}

# 피드 목록 응답 스키마
class FeedListResponse(BaseModel):
    feeds: List[FeedResponse]

# 피드 좋아요 응답 스키마
class FeedResponseWithLike(FeedResponse):
    is_liked: bool

# 피드 목록 좋아요 응답 스키마
class FeedListResponseWithLike(BaseModel):
    feeds: List[FeedResponseWithLike]
    total: int


class FeedCreate(FeedBase):
    file_ids: List[int] = []

class FeedForSitemap(BaseModel):
    id: int
    user_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
