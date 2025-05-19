from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate

def create_comment(db: Session, feed_id: int, content: str, user_id: int):
    db_comment = Comment(feed_id=feed_id, content=content, user_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_feed(db: Session, feed_id: int, skip: int = 0, limit: int = 50):
    """
    특정 피드의 댓글 목록을 조회합니다.
    user 정보를 함께 로드하며, 페이지네이션을 지원합니다.
    최신순(내림차순)으로 정렬합니다.
    """
    return (
        db.query(Comment)
        .filter(Comment.feed_id == feed_id)
        .options(joinedload(Comment.user))  # 사용자 정보 함께 로드
        .order_by(desc(Comment.created_at))  # 최신순 정렬
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_comment(db: Session, comment_id: int, comment_update: CommentUpdate):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment:
        db_comment.content = comment_update.content
        db.commit()
        db.refresh(db_comment)
    return db_comment

def delete_comment(db: Session, comment_id: int):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment:
        db.delete(db_comment)
        db.commit()
    return db_comment
