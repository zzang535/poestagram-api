from fastapi import APIRouter, File as FastAPIFile, UploadFile, HTTPException
from typing import List
from app.schemas.file import FileUploadResponse, File
from app.services.s3 import upload_files_to_s3
from app.models.file import File as FileModel
from app.db.base import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import logging
import re
from PIL import Image
import io

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

async def get_image_dimensions(file: UploadFile) -> tuple:
    """
    이미지 파일의 크기 정보를 반환합니다.
    """
    try:
        # 파일 내용을 메모리에 로드
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
        return width, height
    except Exception as e:
        logger.warning(f"이미지 크기 확인 중 오류 발생: {str(e)}")
        return None, None
    finally:
        # 파일 포인터를 처음 위치로 되돌림
        await file.seek(0)

@router.post("/upload", response_model=FileUploadResponse)
async def upload_files(
    files: List[UploadFile] = FastAPIFile(...),
    db: Session = Depends(get_db)
):
    """
    여러 파일을 S3에 업로드하고 파일 정보를 DB에 저장하는 API
    """
    try:
        logger.info(f"파일 업로드 요청: {len(files)}개 파일")

        for file in files:
            # 파일 메타데이터 출력
            logger.info(f"파일 메타데이터: {file.filename}")
            logger.info(f"- Content-Type: {file.content_type}")
            logger.info(f"- 파일 크기: {file.size} bytes")
            
            # 이미지 파일인 경우 크기 정보 확인
            width, height = None, None
            if file.content_type and file.content_type.startswith('image/'):
                width, height = await get_image_dimensions(file)
                if width and height:
                    logger.info(f"- 이미지 크기: {width}x{height} pixels")

        # 파일 업로드
        file_urls = await upload_files_to_s3(files)
        
        # 파일 정보를 DB에 저장
        uploaded_files = []
        for file, file_url in zip(files, file_urls):
            # URL을 base_url과 s3_key로 분리
            base_url, s3_key = split_file_url(file_url)

            file_info = FileModel(
                file_name=file.filename,
                base_url=base_url,
                s3_key=s3_key,
                content_type=file.content_type,
                file_size=file.size,
                width=width,
                height=height
            )
            db.add(file_info)
            db.flush()  # ID를 즉시 생성하기 위해 flush
            uploaded_files.append(file_info)
        
        db.commit()
        
        logger.info(f"파일 업로드 완료: {len(file_urls)}개 파일")
        return FileUploadResponse(
            message=f"{len(file_urls)}개의 파일이 업로드되었습니다.",
            file_urls=file_urls,
            uploaded_files=uploaded_files
        )
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 