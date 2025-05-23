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

class EmailCheckRequest(BaseModel):
    email: EmailStr

class EmailCheckResponse(BaseModel):
    exists: bool
    message: str

class LoginRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    message: str
    user_id: int
    email: str
    nickname: str
    access_token: str
    token_type: str

# ... 나머지 코드 ... 