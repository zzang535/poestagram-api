from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse
)
from app.services.auth import get_current_user_id
from app.schemas.user import User
from app.models.comment import Comment
from app.models.comment_like import CommentLike
router = APIRouter()

@router.delete("/{comment_id}", status_code=200, summary="댓글 삭제")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    댓글을 삭제합니다.
    
    - 작성자만 자신의 댓글을 삭제할 수 있습니다.
    - 댓글이 존재하지 않거나 권한이 없는 경우 404 오류를 반환합니다.
    """
    # 댓글 조회
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    # 댓글이 존재하지 않는 경우
    if not db_comment:
        raise HTTPException(
            status_code=404,
            detail="댓글을 찾을 수 없습니다."
        )
    
    # 작성자 권한 확인
    if db_comment.user_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="댓글 삭제 권한이 없습니다."
        )
    
    # 댓글 삭제
    db.delete(db_comment)
    db.commit()
    
    return {"message": "댓글이 삭제되었습니다."}



@router.post("/{comment_id}/like", status_code=201, summary="댓글 좋아요")
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    댓글에 좋아요를 추가합니다.

    - 로그인한 사용자만 가능
    - 이미 좋아요한 경우 에러 발생
    """

    # 댓글 존재 확인
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    # 중복 좋아요 방지
    existing_like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_id == current_user_id
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="이미 좋아요한 댓글입니다.")

    # 좋아요 추가
    new_like = CommentLike(comment_id=comment_id, user_id=current_user_id)
    db.add(new_like)
    db.commit()

    return {"message": "댓글에 좋아요를 등록했습니다."}



@router.delete("/{comment_id}/like", status_code=200, summary="댓글 좋아요 취소")
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    댓글에 좋아요를 취소합니다.
    """

    existing_like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_id == current_user_id
    ).first()

    if not existing_like:
        raise HTTPException(status_code=404, detail="좋아요 기록이 없습니다.")

    db.delete(existing_like)
    db.commit()

    return {"message": "댓글 좋아요를 취소했습니다."}
