import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.verify import Verify
from sqlalchemy.orm import Session

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
            verification_code=verification_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
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