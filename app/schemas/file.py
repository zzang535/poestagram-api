from pydantic import BaseModel
from typing import List

class FileUploadResponse(BaseModel):
    message: str
    file_urls: List[str] 