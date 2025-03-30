import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from app.core.config import settings

def generate_verification_code():
    """6자리 랜덤 인증번호 생성"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email: str, verification_code: str):
    """이메일로 인증번호 전송"""
    # 이메일 설정
    sender_email = settings.EMAIL_USER
    sender_password = settings.EMAIL_PASSWORD
    
    # 이메일 메시지 생성
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
    
    try:
        # SMTP 서버 연결 및 이메일 전송
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"이메일 전송 실패: {str(e)}")
        return False 