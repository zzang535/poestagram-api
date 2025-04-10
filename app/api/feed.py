from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.schemas.feed import FeedCreate, FeedResponse  # 스키마는 아직 만들어야 함
from app.services.auth import get_current_user_id

router = APIRouter()

@router.post("/", response_model=FeedResponse, status_code=201)
def create_feed_endpoint(
    feed_data: FeedCreate, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    피드 생성 API 
    """

    new_feed = Feed(
        description=feed_data.description,
        user_id=current_user_id,
    )

    db.add(new_feed)
    db.commit()
    db.refresh(new_feed)

    if feed_data.file_ids:
        files = db.query(File).filter(File.id.in_(feed_data.file_ids)).all()
        for file in files:
            file.feed_id = new_feed.id
            
        db.commit()
    
    return FeedResponse.from_orm(new_feed)