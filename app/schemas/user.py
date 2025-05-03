from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    nickname: str
    email: EmailStr
    # Pydantic v2: ORM 객체에서 속성으로 꺼내올 때 필요
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    terms_of_service: bool # 모델 기준으로 추가
    privacy_policy: bool # 모델 기준으로 추가

class UserUpdate(UserBase):
    nickname: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    terms_of_service: bool # 모델 기준으로 추가
    privacy_policy: bool # 모델 기준으로 추가

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass # UserInDBBase의 모든 필드를 포함

class UserInDB(UserInDBBase):
    pass # UserInDBBase의 모든 필드를 포함