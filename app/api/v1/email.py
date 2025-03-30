from fastapi import APIRouter, HTTPException
from app.schemas.email import EmailVerificationRequest, EmailVerificationResponse
from app.core.email import generate_verification_code, send_verification_email

router = APIRouter()

@router.post("/send-verification", response_model=EmailVerificationResponse)
async def send_verification(request: EmailVerificationRequest):
    try:
        # 인증번호 생성
        verification_code = generate_verification_code()
        
        # 이메일 전송
        success = send_verification_email(request.email, verification_code)
        
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