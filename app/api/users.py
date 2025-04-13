from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.schemas.feed import FeedListResponse

router = APIRouter()

@router.get("/{user_id}/feeds", response_model=FeedListResponse)
def get_user_feeds(
    user_id: int,
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    특정 유저의 모든 피드를 파일 포함하여 가져오는 API
    """
    # 해당 유저가 존재하는지 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 해당 유저의 피드 총 개수 계산
    total_feeds = db.query(Feed).filter(Feed.user_id == user_id).count()
    
    # 해당 유저의 피드 목록과 연결된 파일 정보 함께 가져오기 (생성 날짜 내림차순으로 정렬)
    feeds = (
        db.query(Feed)
        .filter(Feed.user_id == user_id)
        .options(joinedload(Feed.files))  # 피드와 연결된 파일 정보를 한 번에 가져옴
        .order_by(Feed.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # 응답 반환
    return FeedListResponse(feeds=feeds, total=total_feeds) 


@router.get("/{user_id}/feeds/index")
def get_feed_index(
    user_id: int,
    feed_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 유저의 피드 목록에서 특정 피드의 index(위치)를 반환하는 API
    (최신순 정렬 기준)
    """

    print(f"user_id: {user_id}, feed_id: {feed_id}")
    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 기준 피드 확인
    target_feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == user_id
    ).first()
    if not target_feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다")

    # 기준 피드의 created_at보다 이후(created_at > target_feed.created_at)인 피드 개수 카운트
    index = db.query(Feed).filter(
        Feed.user_id == user_id,
        Feed.created_at > target_feed.created_at
    ).count()

    return { "index": index }