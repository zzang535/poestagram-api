from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from .feed_like import FeedLike # FeedLike 모델 임포트

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    nickname = Column(String(50), unique=True, nullable=False)
    terms_of_service = Column(Boolean, nullable=False, default=False)
    privacy_policy = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    feeds = relationship("Feed", back_populates="user", cascade="all, delete-orphan")
    # 사용자가 좋아요 누른 피드 목록 (다대다)
    liked_feeds = relationship(
        "Feed", 
        secondary="feed_likes", # 중간 테이블 이름 지정
        back_populates="liked_by_users"
    ) 