from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.user import User # 사용자 스키마 임포트


class CommentBase(BaseModel):
    content: str # 사용자 입력용 기본 스키마

class CommentCreate(CommentBase):
    pass

class CommentUpdate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    feed_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: User # 댓글 작성자

    class Config:
        from_attributes = True

class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    
    
