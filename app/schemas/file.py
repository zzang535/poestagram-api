from pydantic import BaseModel, computed_field
from typing import List, Optional
from datetime import datetime
from app.core.config import settings

class FileBase(BaseModel):
    file_name: str
    s3_key: str
    s3_key_thumbnail: Optional[str] = None
    content_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None

    @computed_field
    @property
    def url(self) -> str:
        """미디어 Base URL과 s3_key를 조합하여 완전한 URL 생성"""
        return f"{settings.MEDIA_BASE_URL}/{self.s3_key}"

    @computed_field
    @property
    def url_thumbnail(self) -> Optional[str]:
        """썸네일 URL 생성 (s3_key_thumbnail이 있는 경우)"""
        if self.s3_key_thumbnail:
            return f"{settings.MEDIA_BASE_URL}/{self.s3_key_thumbnail}"
        return None

class FileCreate(FileBase):
    pass

class FileInDB(FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic v2용 설정
    model_config = {
        "from_attributes": True
    }

class File(FileInDB):
    pass

class FileUploadResponse(BaseModel):
    message: str
    file_urls: List[str]
    uploaded_files: List[File] 