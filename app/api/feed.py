from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import exists, select, case, desc
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime
import logging

from app.db.base import get_db
from app.models.feed import Feed
from app.models.file import File as FileModel
from app.models.user import User
from app.models.comment import Comment
from app.schemas.file import File as FileSchema
from app.schemas.user import User as UserSchema, UserForFeed as UserSchemaForFeed, UserForFeed
from app.models.feed_like import FeedLike
from app.services.auth import get_current_user_id, get_optional_current_user_id
from app.schemas.feed import (
    FeedCreate,
    FeedResponse,
    FeedResponseWithLike,
    FeedListResponseWithLike,
    FeedForSitemap
)
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse
)
from app.models.comment_like import CommentLike
from app.schemas.comment import (
    CommentResponseWithLike,
    CommentListResponseWithLike
)
from app.services.s3 import delete_file_from_s3
from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/for-sitemap", response_model=List[FeedForSitemap], summary="모든 피드 정보를 사이트맵용으로 조회")
def get_feeds_for_sitemap(db: Session = Depends(get_db)):
    """
    사이트맵 생성을 위해 모든 피드의 ID, 사용자 ID, 마지막 수정일을 반환합니다.
    """
    feeds = db.query(Feed.id, Feed.user_id, Feed.updated_at).all()
    return [{"id": feed.id, "user_id": feed.user_id, "updated_at": feed.updated_at} for feed in feeds]

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

    # 전체 피드 수 계산
    total_feeds = db.query(Feed).count()

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
            .options(joinedload(Feed.user).joinedload(User.profile_file), joinedload(Feed.files))
            .order_by(Feed.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        # 결과 처리: feed, is_liked, likes_count 순서로 튜플 반환
        for feed, is_liked_val, likes_count_val in query.all():
            files = [FileSchema.model_validate(f) for f in feed.files]
            
            # 프로필 이미지 URL 생성
            profile_image_url = None
            if feed.user.profile_file:
                profile_image_url = settings.get_profile_image_url(feed.user.profile_file.s3_key)
            
            user = UserSchemaForFeed(
                id=feed.user.id,
                username=feed.user.username,
                email=feed.user.email,
                bio=feed.user.bio,
                created_at=feed.user.created_at,
                updated_at=feed.user.updated_at,
                terms_of_service=feed.user.terms_of_service,
                privacy_policy=feed.user.privacy_policy,
                profile_image_url=profile_image_url
            )
            
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
            .options(joinedload(Feed.user).joinedload(User.profile_file), joinedload(Feed.files))
            .order_by(Feed.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        # 결과 처리: feed, likes_count 순서로 튜플 반환
        for feed, likes_count_val in query.all():
            files = [FileSchema.model_validate(f) for f in feed.files]
            
            # 프로필 이미지 URL 생성
            profile_image_url = None
            if feed.user.profile_file:
                profile_image_url = settings.get_profile_image_url(feed.user.profile_file.s3_key)
            
            user = UserSchemaForFeed(
                id=feed.user.id,
                username=feed.user.username,
                email=feed.user.email,
                bio=feed.user.bio,
                created_at=feed.user.created_at,
                updated_at=feed.user.updated_at,
                terms_of_service=feed.user.terms_of_service,
                privacy_policy=feed.user.privacy_policy,
                profile_image_url=profile_image_url
            )
            
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

    return FeedListResponseWithLike(feeds=response_feeds, total=total_feeds)

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
        files = db.query(FileModel).filter(FileModel.id.in_(feed_data.file_ids)).all()
        for file in files:
            file.feed_id = new_feed.id
            
        db.commit()
    
    return FeedResponse.from_orm(new_feed)

@router.get("/{feed_id}", response_model=FeedResponseWithLike)
def get_single_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    특정 피드 하나의 정보를 가져오는 API
    """
    # 특정 피드 조회
    feed = (
        db.query(Feed)
        .filter(Feed.id == feed_id)
        .options(
            joinedload(Feed.files),  # 피드와 연결된 파일 정보를 한 번에 가져옴
            joinedload(Feed.user).joinedload(User.profile_file)  # 사용자와 프로필 파일 정보 함께 가져옴
        )
        .first()
    )
    
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다")
    
    # current_user_id가 있을 경우 좋아요 정보 확인
    is_liked = False
    if current_user_id:
        like_exists = (
            db.query(FeedLike)
            .filter(FeedLike.user_id == current_user_id, FeedLike.feed_id == feed_id)
            .first()
        )
        is_liked = like_exists is not None
    
    # 피드 좋아요 수 계산
    likes_count = db.query(FeedLike).filter(FeedLike.feed_id == feed_id).count()
    
    # 프로필 이미지 URL 생성
    profile_image_url = None
    if feed.user.profile_file:
        profile_image_url = settings.get_profile_image_url(feed.user.profile_file.s3_key)
    
    # UserForFeed 스키마 생성
    user_data = UserForFeed(
        id=feed.user.id,
        username=feed.user.username,
        created_at=feed.user.created_at,
        updated_at=feed.user.updated_at,
        profile_image_url=profile_image_url
    )
    
    # FeedResponseWithLike 생성
    feed_response = FeedResponseWithLike(
        id=feed.id,
        description=feed.description,
        frame_ratio=feed.frame_ratio,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
        files=feed.files,
        user=user_data,
        likes_count=likes_count,
        is_liked=is_liked
    )
    
    return feed_response

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
    


@router.post("/{feed_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    feed_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    피드에 댓글 생성
    """ 
    # 피드 존재 여부 확인
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")
    
    # 댓글 생성
    db_comment = Comment(
        feed_id=feed_id, 
        content=comment.content, 
        user_id=current_user_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    # 댓글과 관련된 사용자 정보 및 프로필 파일 로드
    db_comment = db.query(Comment).options(
        joinedload(Comment.user).joinedload(User.profile_file)
    ).filter(Comment.id == db_comment.id).first()
    
    # 프로필 이미지 URL 생성
    profile_image_url = None
    if db_comment.user.profile_file:
        profile_image_url = f"{db_comment.user.profile_file.base_url}/{db_comment.user.profile_file.s3_key}"
    
    # UserForFeed 스키마로 사용자 정보 생성
    user_data = UserForFeed(
        id=db_comment.user.id,
        username=db_comment.user.username,
        created_at=db_comment.user.created_at,
        updated_at=db_comment.user.updated_at,
        profile_image_url=profile_image_url
    )
    
    # CommentResponse 생성
    return CommentResponse(
        id=db_comment.id,
        feed_id=db_comment.feed_id,
        user_id=db_comment.user_id,
        content=db_comment.content,
        created_at=db_comment.created_at,
        updated_at=db_comment.updated_at,
        user=user_data
    )


@router.get(
    "/{feed_id}/comments", 
    response_model=CommentListResponseWithLike,
    summary="피드 댓글 목록 조회"
)
def get_feed_comments(
    feed_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_optional_current_user_id)
):
    """
    특정 피드의 댓글 목록을 조회합니다.
    
    - 페이지네이션을 지원합니다.
    - 댓글은 최신순(작성일 내림차순)으로 정렬됩니다.
    - 로그인 시 내가 좋아요를 눌렀는지 포함됩니다.
    """


    print(f"current_user_id: {current_user_id}")
    # 피드 존재 확인
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="피드를 찾을 수 없습니다.")

    # 댓글 + 작성자 + 프로필 파일 로드
    comments = (
        db.query(Comment)
        .filter(Comment.feed_id == feed_id)
        .options(joinedload(Comment.user).joinedload(User.profile_file))
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for comment in comments:
        # 좋아요 개수
        likes_count = db.query(func.count()).filter(
            CommentLike.comment_id == comment.id
        ).scalar()

        # 내가 좋아요 눌렀는지 여부 (로그인한 경우만)
        is_liked = False
        if current_user_id:
            is_liked = db.query(
                exists().where(
                    (CommentLike.comment_id == comment.id) &
                    (CommentLike.user_id == current_user_id)
                )
            ).scalar()

        # 프로필 이미지 URL 생성
        profile_image_url = None
        if comment.user.profile_file:
            profile_image_url = f"{comment.user.profile_file.base_url}/{comment.user.profile_file.s3_key}"
        
        # UserForFeed 스키마로 사용자 정보 생성
        user_data = UserForFeed(
            id=comment.user.id,
            username=comment.user.username,
            created_at=comment.user.created_at,
            updated_at=comment.user.updated_at,
            profile_image_url=profile_image_url
        )

        result.append(CommentResponseWithLike(
            id=comment.id,
            feed_id=comment.feed_id,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            user=user_data,
            likes_count=likes_count,
            is_liked=is_liked
        ))

    return CommentListResponseWithLike(comments=result)

@router.delete("/{feed_id}", status_code=200, summary="피드 삭제")
def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id) # 피드 작성자 확인을 위해 현재 사용자 ID 필요
):
    """
    특정 피드를 삭제합니다.

    - 피드의 작성자만 삭제할 수 있습니다.
    - 피드가 존재하지 않으면 404 오류를 반환합니다.
    - 권한이 없으면 403 오류를 반환합니다.
    - 피드와 연결된 파일들도 S3와 DB에서 함께 삭제됩니다.
    """
    # 1. 피드 조회 (연결된 파일들도 함께 로드)
    feed_to_delete = db.query(Feed).options(joinedload(Feed.files)).filter(Feed.id == feed_id).first()

    # 2. 피드 존재 여부 확인
    if not feed_to_delete:
        raise HTTPException(status_code=404, detail="삭제할 피드를 찾을 수 없습니다.")

    # 3. 피드 작성자 권한 확인
    if feed_to_delete.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="피드를 삭제할 권한이 없습니다.")

    # 4. 피드와 연결된 파일들 정보 저장 (나중에 삭제용)
    feed_files = list(feed_to_delete.files)  # 리스트로 복사
    
    # 5. 피드 삭제 (cascade로 연결된 데이터들도 함께 삭제됨)
    try:
        db.delete(feed_to_delete)
        db.commit()
        logger.info(f"피드 DB 삭제 완료: ID {feed_id}")
        
        # 6. S3에서 관련 파일들 삭제
        for file in feed_files:
            try:
                if file.s3_key:
                    delete_success = delete_file_from_s3(file.s3_key)
                    if delete_success:
                        logger.info(f"피드 파일 S3 삭제 완료: {file.s3_key}")
                    else:
                        logger.warning(f"피드 파일 S3 삭제 실패: {file.s3_key}")
                
                # DB에서 파일 레코드 삭제 (이미 cascade로 삭제되었을 수 있음)
                # 하지만 명시적으로 삭제 시도
                db_file = db.query(FileModel).filter(FileModel.id == file.id).first()
                if db_file:
                    db.delete(db_file)
                    db.commit()
                    logger.info(f"피드 파일 DB 삭제 완료: ID {file.id}")
                
            except Exception as e:
                logger.error(f"피드 파일 삭제 중 오류 발생 (File ID: {file.id}): {str(e)}")
                # 개별 파일 삭제 실패해도 계속 진행
                continue
        
        return {"message": f"피드(ID: {feed_id})와 관련 파일들이 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        logger.error(f"피드 삭제 중 오류 발생: {str(e)}")
        # 데이터베이스 오류 또는 기타 예외 처리
        raise HTTPException(status_code=500, detail=f"피드 삭제 중 오류 발생: {str(e)}")
