from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FileBase(BaseModel):
    file_name: str
    base_url: str
    s3_key: str
    s3_key_thumbnail: Optional[str] = None
    content_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None

class FileCreate(FileBase):
    pass

class FileInDB(FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class File(FileInDB):
    pass

class FileUploadResponse(BaseModel):
    message: str
    file_urls: List[str]
    uploaded_files: List[File] 