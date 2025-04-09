from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.schemas.feed import FeedCreate, FeedResponse  # 스키마는 아직 만들어야 함

router = APIRouter()

@router.post("/", response_model=FeedResponse, status_code=201)
def create_feed_endpoint(
    feed_data: FeedCreate, 
    db: Session = Depends(get_db)
):
    """
    피드 생성 API (더미 응답용)
    """

    print("설명:", feed_data.description)
    print("파일 IDs:", feed_data.file_ids)

    # 더미 응답 생성
    dummy_response = FeedResponse(
        id=999,
        created_at=datetime.utcnow(),
        updated_at=None
    )

    return dummy_response