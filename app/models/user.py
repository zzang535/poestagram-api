from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from .feed_like import FeedLike # FeedLike 모델 임포트

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)  # 사용자 소개글
    profile_file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    terms_of_service = Column(Boolean, nullable=False, default=False)
    privacy_policy = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    profile_file = relationship("File", foreign_keys=[profile_file_id]) # 프로필 이미지 파일 (1:1)
    feeds = relationship("Feed", back_populates="user", cascade="all, delete-orphan") # 사용자가 작성한 피드 목록
    liked_feeds = relationship( # 사용자가 좋아요 누른 피드 목록 (다대다)
        "Feed", 
        secondary="feed_likes", # 중간 테이블 이름 지정
        back_populates="liked_by_users"
    ) 
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan") # 사용자가 작성한 댓글 목록
    liked_comments = relationship( # 사용자가 좋아요 누른 댓글 목록 (다대다)
        "Comment",
        secondary="comment_likes", # 중간 테이블 이름 지정
        back_populates="liked_by_users"
    )