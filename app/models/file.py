from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from datetime import datetime

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    s3_key = Column(String(255), nullable=False)
    s3_key_thumbnail = Column(String(255), nullable=True)  # 썸네일 S3 키 추가
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)  # 이미지 너비
    height = Column(Integer, nullable=True)  # 이미지 높이
    feed_id = Column(Integer, ForeignKey('feeds.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    feed = relationship("Feed", back_populates="files")
    profile_user = relationship("User", back_populates="profile_file", foreign_keys="User.profile_file_id")