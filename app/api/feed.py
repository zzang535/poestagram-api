from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import exists, select, case
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models.feed import Feed
from app.models.file import File as FileModel
from app.models.user import User as UserModel
from app.schemas.file import File as FileSchema
from app.schemas.user import User as UserSchema
from app.models.feed_like import FeedLike
from app.schemas.feed import (
    FeedCreate,
    FeedResponse,
    FeedResponseWithLike,
    FeedListResponseWithLike
)
from app.services.auth import get_current_user_id, get_optional_current_user_id

router = APIRouter()

@router.get("/", response_model=FeedListResponseWithLike)
def get_all_feeds(
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    모든 피드를 파일 포함하여 가져오는 API.
    사용자 인증 시 좋아요 정보 포함, 각 피드별 전체 좋아요 수 포함.
    """
    print(f"current_user_id: {current_user_id}")

    response_feeds = []

    # 각 피드의 전체 좋아요 수를 계산하는 서브쿼리
    # 이 서브쿼리는 외부 쿼리의 Feed.id를 참조하므로 상관 서브쿼리(correlated subquery)입니다.
    likes_count_subquery = (
        select(func.count(FeedLike.feed_id))
        .where(FeedLike.feed_id == Feed.id)
        .correlate(Feed) # Feed 모델과 명시적으로 연결
        .as_scalar() # 스칼라 값으로 반환하도록 설정
        .label("likes_count")
    )

    if current_user_id is not None:
        print(f"current_user_id is not None: {current_user_id}")
        Like = aliased(FeedLike)
        query = (
            db.query(Feed)
            .outerjoin(
                Like,
                (Feed.id == Like.feed_id) & (Like.user_id == current_user_id)
            )
            .add_columns(
                Like.feed_id.isnot(None).label("is_liked"),
                likes_count_subquery # 전체 좋아요 수 서브쿼리 추가
            )
            .options(joinedload(Feed.user), joinedload(Feed.files))
            .order_by(Feed.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        # 결과 처리: feed, is_liked, likes_count 순서로 튜플 반환
        for feed, is_liked_val, likes_count_val in query.all():
            files = [FileSchema.model_validate(f) for f in feed.files]
            user = UserSchema.model_validate(feed.user)
            dump = FeedResponse(
                id=feed.id,
                description=feed.description,
                frame_ratio=feed.frame_ratio,
                created_at=feed.created_at,
                updated_at=feed.updated_at,
                files=files,
                user=user,
                likes_count=likes_count_val if likes_count_val is not None else 0 # likes_count_val 매핑
            ).model_dump()
            response_feeds.append(FeedResponseWithLike(**dump, is_liked=bool(is_liked_val)))

    else:
        # 사용자가 로그인하지 않은 경우
        query = (
            db.query(Feed)
            .add_columns(likes_count_subquery) # 전체 좋아요 수 서브쿼리 추가
            .options(joinedload(Feed.user), joinedload(Feed.files))
            .order_by(Feed.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        # 결과 처리: feed, likes_count 순서로 튜플 반환
        for feed, likes_count_val in query.all():
            files = [FileSchema.model_validate(f) for f in feed.files]
            user = UserSchema.model_validate(feed.user)
            dump = FeedResponse(
                id=feed.id,
                description=feed.description,
                frame_ratio=feed.frame_ratio,
                created_at=feed.created_at,
                updated_at=feed.updated_at,
                files=files,
                user=user,
                likes_count=likes_count_val if likes_count_val is not None else 0 # likes_count_val 매핑
            ).model_dump()
            response_feeds.append(FeedResponseWithLike(**dump, is_liked=False))

    return FeedListResponseWithLike(feeds=response_feeds)

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
        frame_ratio=feed_data.frame_ratio
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

@router.post("/{feed_id}/like", status_code=200, summary="피드 좋아요 추가")
def like_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    특정 피드에 좋아요를 추가합니다.

    - 사용자가 이미 해당 피드에 좋아요를 눌렀다면 아무 작업도 하지 않고 성공 응답을 반환합니다.
    - 피드가 존재하지 않으면 404 오류를 반환합니다.
    """
    # 1. 피드 존재 확인
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")

    # 2. 이미 좋아요를 눌렀는지 확인
    existing_like = db.query(FeedLike).filter(
        FeedLike.user_id == current_user_id,
        FeedLike.feed_id == feed_id
    ).first()

    if existing_like:
        return {"message": "이미 좋아요를 누른 피드입니다."}

    # 3. 좋아요 정보 생성 및 저장
    new_like = FeedLike(user_id=current_user_id, feed_id=feed_id)
    try:
        db.add(new_like)
        db.commit()
        return {"message": "피드에 좋아요를 추가했습니다."}
    except Exception as e:
        db.rollback()
        # IntegrityError (e.g., user or feed deleted concurrently) or other DB errors
        raise HTTPException(status_code=500, detail=f"좋아요 추가 중 오류 발생: {str(e)}")


@router.delete("/{feed_id}/like", status_code=200, summary="피드 좋아요 취소")
def unlike_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    특정 피드에 대한 좋아요를 취소합니다.

    - 사용자가 해당 피드에 좋아요를 누르지 않았다면 아무 작업도 하지 않고 성공 응답을 반환합니다.
    - 피드가 존재하지 않으면 404 오류를 반환합니다.
    """
    # 1. 피드 존재 확인 (선택적이지만, 좋아요 레코드 검색 전에 하는 것이 좋음)
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")

    # 2. 좋아요 기록 찾기
    like_to_delete = db.query(FeedLike).filter(
        FeedLike.user_id == current_user_id,
        FeedLike.feed_id == feed_id
    ).first()

    if not like_to_delete:
        return {"message": "좋아요를 누르지 않은 피드입니다."}

    # 3. 좋아요 기록 삭제
    try:
        db.delete(like_to_delete)
        db.commit()
        return {"message": "피드 좋아요를 취소했습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"좋아요 취소 중 오류 발생: {str(e)}")