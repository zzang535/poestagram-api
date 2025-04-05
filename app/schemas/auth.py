from pydantic import BaseModel, EmailStr

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
    nickname: str
    terms_of_service: bool
    privacy_policy: bool

class SignUpResponse(BaseModel):
    message: str
    user_id: int
    access_token: str
    token_type: str

# ... 나머지 코드 ... 