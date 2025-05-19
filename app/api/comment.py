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

router = APIRouter()

@router.delete("/comments/{comment_id}", status_code=200, summary="댓글 삭제")
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

