from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Poestagram API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str
    DB_HOST: str
    
    # Email settings
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24 * 7  # 7일
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 10  # test
    
    # AWS settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    
    # Media settings
    IMAGE_BASE_URL: str  # CloudFront URL for images and thumbnails
    STORAGE_BASE_URL: str  # CloudFront URL for videos
    
    def get_profile_image_url(self, s3_key: str) -> str:
        """프로필 이미지 URL 생성 (항상 IMAGE_BASE_URL 사용)"""
        return f"{self.IMAGE_BASE_URL}/{s3_key}"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_DATABASE}"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()   