from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, Any

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationResponse(BaseModel):
    message: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class VerifyCodeResponse(BaseModel):
    is_verified: bool
    message: str

class SignUpRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    terms_of_service: bool
    privacy_policy: bool

class SignUpResponse(BaseModel):
    message: str
    user_id: int

class EmailCheckRequest(BaseModel):
    email: EmailStr

class EmailCheckResponse(BaseModel):
    exists: bool
    message: str

class UsernameCheckRequest(BaseModel):
    username: str

class UsernameCheckResponse(BaseModel):
    exists: bool
    message: str

class LoginRequest(BaseModel):
    identifier: str
    password: str

class LoginResponse(BaseModel):
    message: str
    user_id: int
    email: str
    username: str
    profile_image_url: Optional[str] = None
    access_token: str
    token_type: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str

# ... 나머지 코드 ... 