from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Poe2stagram API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str
    DB_HOST: str
    
    # Email settings
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_DATABASE}"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 