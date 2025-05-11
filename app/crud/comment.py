from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate

def create_comment(db: Session, feed_id: int, content: str, user_id: int):
    db_comment = Comment(feed_id=feed_id, content=content, user_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_feed(db: Session, feed_id: int):
    return db.query(Comment).filter(Comment.feed_id == feed_id).order_by(Comment.created_at).all()

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
