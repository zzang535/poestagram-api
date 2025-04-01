from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class Verify(Base):
    __tablename__ = "verifies"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    code = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 