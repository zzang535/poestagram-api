from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from .feed_like import FeedLike

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(1000), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    frame_ratio = Column(Float, nullable=False, server_default='1.0')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    user = relationship("User", back_populates="feeds")
    files = relationship("File", back_populates="feed", cascade="all, delete-orphan")

    # 피드를 좋아요 누른 사용자 목록 (다대다)
    liked_by_users = relationship(
        "User", 
        secondary="feed_likes", # 중간 테이블 이름 지정
        back_populates="liked_feeds"
    ) 
    comments = relationship("Comment", back_populates="feed", cascade="all, delete-orphan") # 피드에 달린 댓글 목록