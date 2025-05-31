from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    # Pydantic v2: ORM 객체에서 속성으로 꺼내올 때 필요
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    terms_of_service: bool # 모델 기준으로 추가
    privacy_policy: bool # 모델 기준으로 추가

class UserUpdate(UserBase):
    username: Optional[str] = None

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

class UserProfileResponse(UserBase):
    id: int
    profile_image_url: Optional[str] = None
    feeds_count: int
    created_at: datetime
    # 필요하다면 다른 필드 추가 가능 (예: 팔로워 수, 팔로잉 수)

    class Config:
        from_attributes = True

class ProfileImageUpdateResponse(BaseModel):
    message: str
    profile_image_url: Optional[str] = None

class UsernameUpdateRequest(BaseModel):
    username: str

class UsernameUpdateResponse(BaseModel):
    message: str
    username: str