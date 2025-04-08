from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.schemas.file import FileUploadResponse
from app.services.s3 import upload_files_to_s3
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    여러 파일을 S3에 업로드하는 API
    """
    try:
        logger.info(f"파일 업로드 요청: {len(files)}개 파일")
        
        # 파일 업로드
        file_urls = await upload_files_to_s3(files)
        
        logger.info(f"파일 업로드 완료: {len(file_urls)}개 파일")
        return FileUploadResponse(
            message=f"{len(file_urls)}개의 파일이 업로드되었습니다.",
            file_urls=file_urls
        )
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 