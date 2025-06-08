from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, File as FastAPIFile, UploadFile
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.sql import func
from typing import List, Optional

from app.db.base import get_db
from app.models.feed import Feed
from app.models.user import User
from app.models.file import File
from app.models.file import File as FileModel
from app.models.feed_like import FeedLike

from app.schemas.feed import FeedListResponse, FeedResponseWithLike, FeedListResponseWithLike
from app.schemas.user import (
    UserProfileResponse, 
    ProfileImageUpdateResponse, 
    UsernameUpdateRequest, 
    UsernameUpdateResponse, 
    BioUpdateRequest, 
    BioUpdateResponse,
    UserForFeed
)

from app.services.auth import get_current_user_id, get_optional_current_user_id
from app.services.s3 import upload_files_to_s3, delete_file_from_s3
from app.services.media import split_file_url, get_image_dimensions


# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()



@router.get("/{user_id}/feeds", response_model=FeedListResponseWithLike)
def get_user_feeds(
    user_id: int,
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
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
    
    # 해당 유저의 피드 목록과 연결된 파일 정보, 사용자 프로필 정보 함께 가져오기 (생성 날짜 내림차순으로 정렬)
    feeds = (
        db.query(Feed)
        .filter(Feed.user_id == user_id)
        .options(
            joinedload(Feed.files),  # 피드와 연결된 파일 정보를 한 번에 가져옴
            joinedload(Feed.user).joinedload(User.profile_file)  # 사용자와 프로필 파일 정보 함께 가져옴
        )
        .order_by(Feed.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # current_user_id가 있을 경우 좋아요 정보 미리 로딩해둠
    # 다음 쿼리에서 사용
    liked_feed_ids = set()
    if current_user_id:
        liked_rows = (
            db.query(FeedLike.feed_id)
            .filter(
                FeedLike.user_id == current_user_id,
                FeedLike.feed_id.in_([feed.id for feed in feeds])
            )
            .all()
        )
        liked_feed_ids = {row.feed_id for row in liked_rows} 

    print(f"liked_feed_ids: {liked_feed_ids}")
    
    # 피드 전체 좋아요 수 계산
    feed_ids = [feed.id for feed in feeds]
    likes_count_by_feed = dict(
        db.query(FeedLike.feed_id, func.count())
        .filter(FeedLike.feed_id.in_(feed_ids))
        .group_by(FeedLike.feed_id)
        .all()
    )

    # 피드 응답 생성 (프로필 이미지 URL 포함)
    feed_responses = []
    for feed in feeds:
        # 프로필 이미지 URL 생성
        profile_image_url = None
        if feed.user.profile_file:
            profile_image_url = f"{feed.user.profile_file.base_url}/{feed.user.profile_file.s3_key}"
        
        # UserForFeed 스키마 생성
        from app.schemas.user import UserForFeed
        user_data = UserForFeed(
            id=feed.user.id,
            username=feed.user.username,
            created_at=feed.user.created_at,
            updated_at=feed.user.updated_at,
            profile_image_url=profile_image_url
        )
        
        # FeedResponse 생성
        from app.schemas.feed import FeedResponse
        feed_response = FeedResponseWithLike(
            id=feed.id,
            description=feed.description,
            frame_ratio=feed.frame_ratio,
            created_at=feed.created_at,
            updated_at=feed.updated_at,
            files=feed.files,
            user=user_data,
            likes_count=likes_count_by_feed.get(feed.id, 0),
            is_liked=feed.id in liked_feed_ids  # 추가된 필드
        )
        feed_responses.append(feed_response)
    
    # 응답 반환
    return FeedListResponseWithLike(feeds=feed_responses, total=total_feeds)

@router.put("/profile-image", response_model=ProfileImageUpdateResponse, summary="프로필 사진 변경")
async def update_profile_image(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    현재 로그인한 사용자의 프로필 사진을 변경합니다.
    
    - 이미지 파일만 업로드 가능합니다.
    - 기존 프로필 사진이 있으면 교체됩니다.
    """
    try:
        logger.info(f"프로필 사진 변경 요청: 사용자 ID {current_user_id}, 파일명 {file.filename}")

        # 이미지 파일인지 확인
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

        # 현재 사용자 조회 (기존 프로필 파일 정보 포함)
        user = db.query(User).options(joinedload(User.profile_file)).filter(User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 기존 프로필 파일 정보 저장 (나중에 삭제용)
        old_profile_file = user.profile_file
        old_profile_file_id = user.profile_file_id

        # 이미지 크기 정보 가져오기
        width, height = await get_image_dimensions(file)
        logger.info(f"이미지 크기: {width}x{height} pixels")

        # S3에 파일 업로드
        file_urls = await upload_files_to_s3([file])
        if not file_urls:
            raise HTTPException(status_code=500, detail="파일 업로드에 실패했습니다.")

        # URL을 base_url과 s3_key로 분리
        base_url, s3_key = split_file_url(file_urls[0])

        # 파일 정보를 DB에 저장
        file_info = FileModel(
            file_name=file.filename,
            base_url=base_url,
            s3_key=s3_key,
            content_type=file.content_type,
            file_size=file.size,
            width=width,
            height=height
        )
        db.add(file_info)
        db.flush()  # ID를 즉시 생성

        # 사용자의 profile_file_id 업데이트
        user.profile_file_id = file_info.id
        db.commit()

        # 기존 프로필 파일 정리
        if old_profile_file:
            try:
                # S3에서 기존 파일 삭제
                if old_profile_file.s3_key:
                    delete_success = delete_file_from_s3(old_profile_file.s3_key)
                    if delete_success:
                        logger.info(f"기존 프로필 이미지 S3 삭제 완료: {old_profile_file.s3_key}")
                    else:
                        logger.warning(f"기존 프로필 이미지 S3 삭제 실패: {old_profile_file.s3_key}")
                
                # DB에서 기존 파일 레코드 삭제
                db.delete(old_profile_file)
                db.commit()
                logger.info(f"기존 프로필 파일 DB 삭제 완료: ID {old_profile_file_id}")
                
            except Exception as e:
                logger.error(f"기존 프로필 파일 삭제 중 오류 발생: {str(e)}")
                # 기존 파일 삭제 실패해도 새 파일 업로드는 성공했으므로 계속 진행
        else:
            logger.info(f"사용자 ID {current_user_id}는 기존 프로필 이미지가 없어서 삭제할 파일이 없습니다.")

        # 프로필 이미지 URL 생성
        profile_image_url = f"{base_url}/{s3_key}"

        logger.info(f"프로필 사진 변경 완료: 사용자 ID {current_user_id}, 파일 ID {file_info.id}")
        
        return ProfileImageUpdateResponse(
            message="프로필 사진이 성공적으로 변경되었습니다.",
            profile_image_url=profile_image_url
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"프로필 사진 변경 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로필 사진 변경 중 오류가 발생했습니다: {str(e)}")

@router.put("/username", response_model=UsernameUpdateResponse, summary="유저네임 변경")
async def update_username(
    request: UsernameUpdateRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    현재 로그인한 사용자의 유저네임을 변경합니다.
    
    - 새로운 유저네임이 이미 사용 중인지 확인합니다.
    - 중복된 유저네임이 있으면 400 오류를 반환합니다.
    - 문제없으면 유저네임을 변경합니다.
    """
    try:
        logger.info(f"유저네임 변경 요청: 사용자 ID {current_user_id}, 새 유저네임 {request.username}")

        # 현재 사용자 조회
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 현재 유저네임과 동일한지 확인
        if user.username == request.username:
            raise HTTPException(status_code=400, detail="현재 유저네임과 동일합니다.")

        # 새로운 유저네임이 이미 사용 중인지 확인
        existing_user = db.query(User).filter(
            User.username == request.username,
            User.id != current_user_id  # 본인 제외
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 유저네임입니다.")

        # 유저네임 변경
        old_username = user.username
        user.username = request.username
        db.commit()

        logger.info(f"유저네임 변경 완료: 사용자 ID {current_user_id}, {old_username} → {request.username}")
        
        return UsernameUpdateResponse(
            message="유저네임이 성공적으로 변경되었습니다.",
            username=request.username
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"유저네임 변경 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"유저네임 변경 중 오류가 발생했습니다: {str(e)}")

@router.put("/bio", response_model=BioUpdateResponse, summary="프로필 소개글 변경")
async def update_bio(
    request: BioUpdateRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    현재 로그인한 사용자의 프로필 소개글을 변경합니다.
    
    - bio는 빈 문자열이나 null로 설정할 수 있습니다.
    """
    try:
        logger.info(f"프로필 소개글 변경 요청: 사용자 ID {current_user_id}")

        # 현재 사용자 조회
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # bio 변경
        old_bio = user.bio
        user.bio = request.bio
        db.commit()

        logger.info(f"프로필 소개글 변경 완료: 사용자 ID {current_user_id}")
        
        return BioUpdateResponse(
            message="프로필 소개글이 성공적으로 변경되었습니다.",
            bio=request.bio
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"프로필 소개글 변경 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로필 소개글 변경 중 오류가 발생했습니다: {str(e)}")

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
        # File 모델의 base_url과 s3_key를 조합하여 완전한 URL 생성
        profile_image_url = f"{user.profile_file.base_url}/{user.profile_file.s3_key}"

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        bio=user.bio,
        profile_image_url=profile_image_url,
        feeds_count=feeds_count,
        created_at=user.created_at
        # UserBase에서 상속받은 다른 필드들도 자동으로 포함될 수 있으나,
        # 명시적으로 전달하는 것이 더 안전할 수 있음 (Pydantic 버전에 따라 다름)
        # 만약 UserBase의 필드가 자동으로 매핑되지 않는다면, 여기서 명시적으로 추가 필요
    )


@router.get("/{user_id}/feeds/{feed_id}/index")
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