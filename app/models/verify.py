from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class Verify(Base):
    __tablename__ = "verify"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True)
    verification_code = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # 5분 후 만료 