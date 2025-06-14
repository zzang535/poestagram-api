from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from app.db.base import get_db
from app.schemas.auth import (
    EmailVerificationRequest, EmailVerificationResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    SignUpRequest, SignUpResponse,
    EmailCheckRequest, EmailCheckResponse,
    UsernameCheckRequest, UsernameCheckResponse,
    LoginRequest, LoginResponse,
    PasswordResetRequest, PasswordResetResponse
)
from app.services.auth import (
    generate_verification_code, send_verification_email, 
    create_user, verify_code, check_email_exists, 
    check_username_exists, create_access_token, verify_password,
    reset_password
)
from app.models.verify import Verify
from app.models.user import User
from sqlalchemy import desc
import logging
from fastapi import status
from typing import Optional
import re # 정규표현식 사용을 위해 추가 (더 엄격한 이메일 검증 시)
from app.core.config import settings

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

@router.post("/check-username", response_model=UsernameCheckResponse)
async def check_username(request: UsernameCheckRequest, db: Session = Depends(get_db)):
    """
    사용자명 중복 체크 API
    """
    try:
        logger.info(f"사용자명 중복 체크 요청: {request.username}")
        exists = check_username_exists(db, request.username)
        
        return UsernameCheckResponse(
            exists=exists,
            message="이미 사용 중인 사용자명입니다." if exists else "사용 가능한 사용자명입니다."
        )
    except Exception as e:
        logger.error(f"사용자명 중복 체크 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자명 중복 체크 중 오류가 발생했습니다: {str(e)}")

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
        logger.info(f"회원가입 요청: {request.email}, {request.username}")
        
        # 사용자 생성
        user = create_user(
            db=db,
            email=request.email,
            username=request.username,
            password=request.password,
            terms_of_service=request.terms_of_service,
            privacy_policy=request.privacy_policy
        )
        
        logger.info(f"회원가입 성공: {user.id}")
        return SignUpResponse(
            message="회원가입이 완료되었습니다.",
            user_id=user.id
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
    print("login")
    print(request)
    try:
        user: Optional[User] = None
        identifier = request.identifier
        logger.info(f"로그인 요청: {identifier}")

        # identifier가 이메일 형식인지 간단히 확인 (더 엄격하게 하려면 정규식 사용)
        # 예: is_email = bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", identifier))
        is_email = "@" in identifier and "." in identifier # 간단한 이메일 형식 체크
        
        if is_email:
            logger.info(f"로그인 시도 (이메일): {identifier}")
            user = db.query(User).options(joinedload(User.profile_file)).filter(User.email == identifier).first()
        else:
            logger.info(f"로그인 시도 (사용자명): {identifier}")
            user = db.query(User).options(joinedload(User.profile_file)).filter(User.username == identifier).first()
        
        if not user or not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="로그인 정보가 올바르지 않습니다.",
            )
        
        # 프로필 이미지 URL 생성
        profile_image_url = None
        if user.profile_file:
            profile_image_url = f"{settings.MEDIA_BASE_URL}/{user.profile_file.s3_key}"
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"로그인 성공: {user.id}")
        return LoginResponse(
            message="로그인이 완료되었습니다.",
            user_id=user.id,
            email=user.email,
            username=user.username,
            profile_image_url=profile_image_url,
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {str(e)}")

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password_endpoint(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 비밀번호 변경 API

    - 이메일, 인증 코드, 새 비밀번호를 입력받습니다.
    - 이메일과 인증 코드가 유효하고 인증된 상태인지 확인합니다.
    - 사용자를 찾아 새 비밀번호로 업데이트합니다.
    """

    print("reset-password")
    print(request)
    try:
        logger.info(f"비밀번호 변경 요청: {request.email}")
        success = reset_password(
            db=db,
            email=request.email,
            code=request.code,
            new_password=request.new_password
        )
        if success:
            return PasswordResetResponse(message="비밀번호가 성공적으로 변경되었습니다.")
        else:
            # 이 경우는 change_password 함수 내에서 HTTPException이 발생하여
            # 여기까지 오지 않아야 하지만, 만약을 위해 추가
            raise HTTPException(status_code=500, detail="비밀번호 변경에 실패했습니다.") 
            
    except HTTPException as e:
        raise e # 서비스에서 발생한 HTTPException을 그대로 전달
    except Exception as e:
        logger.error(f"비밀번호 변경 API 처리 중 오류 발생: {request.email}, {str(e)}")
        raise HTTPException(status_code=500, detail=f"비밀번호 변경 처리 중 오류가 발생했습니다: {str(e)}") 