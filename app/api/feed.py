from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.schemas.feed import FeedCreate, FeedResponse, FeedListResponse
from app.services.auth import get_current_user_id

router = APIRouter()

@router.get("/", response_model=FeedListResponse)
def get_all_feeds(
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    모든 피드를 파일 포함하여 가져오는 API
    """
    # 전체 피드 개수 계산
    total_feeds = db.query(Feed).count()
    
    # 피드 목록과 연결된 파일 정보 함께 가져오기 (생성 날짜 내림차순으로 정렬)
    feeds = (
        db.query(Feed)
        .options(joinedload(Feed.files))  # 피드와 연결된 파일 정보를 한 번에 가져옴
        .order_by(Feed.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # 응답 반환
    return FeedListResponse(feeds=feeds, total=total_feeds)

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