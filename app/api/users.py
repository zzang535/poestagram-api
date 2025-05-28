from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.schemas.feed import FeedListResponse
from app.schemas.user import UserProfileResponse

router = APIRouter()

@router.get("/{user_id}", response_model=UserProfileResponse, summary="특정 사용자 정보 조회")
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 프로필 정보를 가져옵니다.
    - 사용자 기본 정보 (id, username, email, profile_image_url)
    - 해당 사용자가 작성한 피드의 총 개수
    """
    user = db.query(User).options(joinedload(User.profile_file)).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    feeds_count = db.query(Feed).filter(Feed.user_id == user_id).count()

    profile_image_url = None
    if user.profile_file:
        # File 모델의 base_url과 s3_key (또는 file_name)을 조합하여 완전한 URL 생성 가정
        # 예시: profile_image_url = f"{user.profile_file.base_url}/{user.profile_file.s3_key}"
        # 여기서는 s3_key_thumbnail 이 있다면 그것을 우선 사용하거나, s3_key를 사용
        s3_key_to_use = user.profile_file.s3_key_thumbnail if user.profile_file.s3_key_thumbnail else user.profile_file.s3_key
        profile_image_url = f"{user.profile_file.base_url}/{s3_key_to_use}"

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        profile_image_url=profile_image_url,
        feeds_count=feeds_count,
        created_at=user.created_at
        # UserBase에서 상속받은 다른 필드들도 자동으로 포함될 수 있으나,
        # 명시적으로 전달하는 것이 더 안전할 수 있음 (Pydantic 버전에 따라 다름)
        # 만약 UserBase의 필드가 자동으로 매핑되지 않는다면, 여기서 명시적으로 추가 필요
    )

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