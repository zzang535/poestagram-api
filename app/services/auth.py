import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.verify import Verify
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError  # PyJWT 전용 예외

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # tokenUrl은 사용 안 해도 됨

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_verification_code():
    """6자리 랜덤 인증번호 생성"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email: str, verification_code: str, db: Session):
    """이메일로 인증번호 전송 및 저장"""
    try:
        # 기존 인증 코드 삭제
        db.query(Verify).filter(Verify.email == email).delete()
        
        # 새로운 인증 정보 저장
        verify = Verify(
            email=email,
            code=verification_code,
            is_verified=False
        )
        db.add(verify)
        db.commit()

        # 이메일 전송 로직...
        sender_email = settings.EMAIL_USER
        sender_password = settings.EMAIL_PASSWORD
        
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = "이메일 인증번호"
        
        body = f"""
        안녕하세요,
        
        요청하신 이메일 인증번호는 다음과 같습니다:
        
        {verification_code}
        
        이 인증번호는 5분간 유효합니다.
        
        감사합니다.
        """
        
        message.attach(MIMEText(body, "plain"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        
        return True
    except Exception as e:
        print(f"이메일 전송 실패: {str(e)}")
        db.rollback()
        return False

def create_user(db: Session, email: str, nickname: str, terms_of_service: bool, privacy_policy: bool):
    """새로운 사용자 생성"""
    try:
        # 이메일 중복 확인
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        
        # 닉네임 중복 확인
        if db.query(User).filter(User.nickname == nickname).first():
            raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
        
        # 필수 약관 동의 확인
        if not terms_of_service or not privacy_policy:
            raise HTTPException(status_code=400, detail="필수 약관에 동의해야 합니다.")
        
        # 이메일 인증 확인
        verify = db.query(Verify).filter(
            Verify.email == email,
            Verify.is_verified == True
        ).first()
        
        if not verify:
            raise HTTPException(status_code=400, detail="이메일 인증이 필요합니다.")
        
        # 사용자 생성
        user = User(
            email=email,
            nickname=nickname,
            terms_of_service=terms_of_service,
            privacy_policy=privacy_policy
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류가 발생했습니다: {str(e)}")

def check_email_exists(db: Session, email: str) -> bool:
    """
    이메일 중복 체크
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        return user is not None
    except Exception as e:
        logger.error(f"이메일 중복 체크 중 오류 발생: {str(e)}")
        raise

def verify_code(db: Session, email: str, code: str) -> bool:
    """
    인증 코드 확인
    """
    try:
        # 해당 이메일의 최신 인증 정보 조회
        verify = db.query(Verify).filter(
            Verify.email == email
        ).order_by(Verify.created_at.desc()).first()
        
        if not verify:
            logger.warning(f"인증 정보 없음: {email}")
            return False
        
        # 인증 코드 비교
        if verify.code != code:
            logger.warning(f"인증 코드 불일치: {email}, 입력: {code}, 저장: {verify.code}")
            return False
        
        # 인증 성공 시 상태 업데이트
        verify.is_verified = True
        db.commit()
        
        logger.info(f"인증 성공: {email}")
        return True
    except Exception as e:
        logger.error(f"인증 코드 확인 중 오류 발생: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"인증 코드 확인 중 오류가 발생했습니다: {str(e)}")

def create_access_token(data: dict) -> str:
    """
    JWT 액세스 토큰 생성
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt 



def get_current_user_id(token: str = Depends(oauth2_scheme)):
    user_id = decode_access_token(token)
    return user_id  # 또는 User 객체로 조회해서 반환해도 됨


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")