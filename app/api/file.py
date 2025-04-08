from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from app.schemas.file import FileUploadResponse
from app.services.s3 import upload_files_to_s3
from app.models.file import File as FileModel
from app.db.base import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# URL 분리 함수
def split_file_url(file_url):
    """
    파일 URL을 base_url과 s3_key로 분리합니다.
    """
    pattern = r'(https?://[^/]+)/(.+)'
    match = re.match(pattern, file_url)
    if match:
        base_url = match.group(1)
        s3_key = match.group(2)
        return base_url, s3_key
    return file_url, ""  # 분리 실패 시 기본값

@router.post("/upload", response_model=FileUploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    여러 파일을 S3에 업로드하고 파일 정보를 DB에 저장하는 API
    """
    try:
        logger.info(f"파일 업로드 요청: {len(files)}개 파일")
        
        # 파일 업로드
        file_urls = await upload_files_to_s3(files)
        
        # 파일 정보를 DB에 저장
        for file, file_url in zip(files, file_urls):
            # URL을 base_url과 s3_key로 분리
            base_url, s3_key = split_file_url(file_url)
            
            file_info = FileModel(
                file_name=file.filename,
                base_url=base_url,
                s3_key=s3_key,
                file_type=file.content_type,
                file_size=file.size
            )
            db.add(file_info)
        
        db.commit()
        
        logger.info(f"파일 업로드 완료: {len(file_urls)}개 파일")
        return FileUploadResponse(
            message=f"{len(file_urls)}개의 파일이 업로드되었습니다.",
            file_urls=file_urls
        )
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 