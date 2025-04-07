from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.auth import (
    EmailVerificationRequest, EmailVerificationResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    SignUpRequest, SignUpResponse,
    EmailCheckRequest, EmailCheckResponse,
    LoginRequest, LoginResponse
)
from app.services.auth import generate_verification_code, send_verification_email, create_user, verify_code, check_email_exists, create_access_token
from app.models.verify import Verify
from app.models.user import User
from sqlalchemy import desc
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/check-email", response_model=EmailCheckResponse)
async def check_email(request: EmailCheckRequest, db: Session = Depends(get_db)):
    """
    이메일 중복 체크 API
    """
    try:
        logger.info(f"이메일 중복 체크 요청: {request.email}")
        exists = check_email_exists(db, request.email)
        
        return EmailCheckResponse(
            exists=exists,
            message="이미 등록된 이메일입니다." if exists else "사용 가능한 이메일입니다."
        )
    except Exception as e:
        logger.error(f"이메일 중복 체크 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이메일 중복 체크 중 오류가 발생했습니다: {str(e)}")

@router.post("/send-verification", response_model=EmailVerificationResponse)
async def send_verification(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """
    이메일 인증 코드 전송 API
    """
    try:
        logger.info(f"이메일 인증 코드 전송 요청: {request.email}")
        verification_code = generate_verification_code()
        success = send_verification_email(request.email, verification_code, db)
        
        if not success:
            raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다.")
        
        return {"message": "인증번호가 이메일로 전송되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"이메일 인증 코드 전송 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이메일 인증 코드 전송 중 오류가 발생했습니다: {str(e)}")

@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"인증 코드 확인 요청: {request.email}, {request.code}")
        
        # 해당 이메일의 최신 인증 정보 조회
        verify = db.query(Verify).filter(
            Verify.email == request.email
        ).order_by(desc(Verify.created_at)).first()
        
        logger.info(f"조회된 인증 정보: {verify}")
        
        if not verify:
            logger.warning(f"인증 정보 없음: {request.email}")
            return VerifyCodeResponse(
                is_verified=False,
                message="인증 정보를 찾을 수 없습니다."
            )
        
        # 인증 코드 비교
        if verify.code != request.code:
            logger.warning(f"인증 코드 불일치: {request.email}, 입력: {request.code}, 저장: {verify.code}")
            return VerifyCodeResponse(
                is_verified=False,
                message="인증번호가 일치하지 않습니다."
            )
        
        # 인증 성공 시 상태 업데이트
        verify.is_verified = True
        db.commit()
        
        logger.info(f"인증 성공: {request.email}")
        return VerifyCodeResponse(
            is_verified=True,
            message="인증이 완료되었습니다."
        )
    except Exception as e:
        logger.error(f"인증 코드 확인 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인증 코드 확인 중 오류가 발생했습니다: {str(e)}")

@router.post("/signup", response_model=SignUpResponse)
async def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"회원가입 요청: {request.email}, {request.nickname}")
        
        # 사용자 생성
        user = create_user(
            db=db,
            email=request.email,
            nickname=request.nickname,
            terms_of_service=request.terms_of_service,
            privacy_policy=request.privacy_policy
        )
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"회원가입 성공: {user.id}")
        return SignUpResponse(
            message="회원가입이 완료되었습니다.",
            user_id=user.id,
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"회원가입 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류가 발생했습니다: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 API
    """
    try:
        logger.info(f"로그인 요청: {request.email}")
        
        # 이메일로 사용자 검색
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"로그인 성공: {user.id}")
        return LoginResponse(
            message="로그인이 완료되었습니다.",
            user_id=user.id,
            email=user.email,
            nickname=user.nickname,
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {str(e)}") 