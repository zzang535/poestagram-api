from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.email import EmailVerificationRequest, EmailVerificationResponse
from app.core.email import generate_verification_code, send_verification_email
from app.core.database import get_db
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class VerifyCodeResponse(BaseModel):
    message: str
    success: bool

@router.post("/send-verification", response_model=EmailVerificationResponse)
async def send_verification(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    try:
        # 인증번호 생성
        verification_code = generate_verification_code()
        
        # 이메일 전송 및 인증 정보 저장
        success = send_verification_email(request.email, verification_code, db)
        
        if success:
            return EmailVerificationResponse(
                message="인증번호가 이메일로 전송되었습니다.",
                success=True
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="이메일 전송에 실패했습니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    verify = db.query(Verify).filter(
        Verify.email == request.email,
        Verify.verification_code == request.code,
        Verify.expires_at > datetime.utcnow()
    ).first()
    
    if verify:
        # 인증 성공 후 해당 인증 정보 삭제
        db.delete(verify)
        db.commit()
        return VerifyCodeResponse(
            message="인증이 완료되었습니다.",
            success=True
        )
    else:
        return VerifyCodeResponse(
            message="잘못된 인증번호이거나 만료된 인증번호입니다.",
            success=False
        ) 