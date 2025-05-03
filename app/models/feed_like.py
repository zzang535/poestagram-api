from sqlalchemy import Column, Integer, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.sql import func
from app.db.base import Base

class FeedLike(Base):
    __tablename__ = "feed_likes"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feed_id = Column(Integer, ForeignKey('feeds.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 복합 기본 키 설정
    __table_args__ = (PrimaryKeyConstraint('user_id', 'feed_id'),) 