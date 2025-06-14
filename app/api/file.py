from fastapi import APIRouter, File as FastAPIFile, UploadFile, HTTPException
from typing import List
from app.schemas.file import FileUploadResponse, File
from app.services.s3 import upload_files_to_s3
from app.services.media import get_image_dimensions, get_video_dimensions_with_rotation, extract_video_thumbnail
from app.models.file import File as FileModel
from app.db.base import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import logging
import os
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def extract_s3_key_from_url(url: str) -> str:
    """S3 URL에서 s3_key를 추출합니다."""
    # URL 형식: https://bucket-name.s3.region.amazonaws.com/uploads/file.jpg
    # s3_key 형식: uploads/file.jpg
    if ".amazonaws.com/" in url:
        return url.split(".amazonaws.com/", 1)[1]
    return url

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

        # 파일 메타데이터를 저장할 리스트
        file_metadata_list = []

        for file in files:
            # 파일 메타데이터 출력
            logger.info(f"파일 메타데이터: {file.filename}")
            logger.info(f"- Content-Type: {file.content_type}")
            logger.info(f"- 파일 크기: {file.size} bytes")
            
            # 이미지 또는 비디오 파일인 경우 크기 정보 확인
            width, height = None, None
            s3_key_thumbnail = None
            
            if file.content_type:
                if file.content_type.startswith('image/'):
                    width, height = await get_image_dimensions(file)
                elif file.content_type.startswith('video/'):
                    # 회전 정보를 고려한 최종 비디오 크기 가져오기
                    width, height = await get_video_dimensions_with_rotation(file)
                    if width is None or height is None:
                        logger.warning(f"비디오 크기 정보를 가져올 수 없습니다: {file.filename}")

                    # 비디오 썸네일 추출 및 업로드 (최종 width, height 전달)
                    thumbnail = await extract_video_thumbnail(file, target_width=width, target_height=height)
                    if thumbnail:
                        try:
                            # 썸네일 업로드 전 원본 파일 포인터 복구 (필요 시)
                            await file.seek(0) # extract_video_thumbnail 내부에서 읽었으므로 필요
                            
                            thumbnail_urls = await upload_files_to_s3([thumbnail])
                            if thumbnail_urls:
                                s3_key_thumbnail = extract_s3_key_from_url(thumbnail_urls[0])
                            await thumbnail.close()
                        except Exception as e:
                            logger.error(f"썸네일 업로드 중 오류 발생: {str(e)}")
                
                if width and height:
                    logger.info(f"- 미디어 크기: {width}x{height} pixels")

            # 메타데이터 저장
            file_metadata_list.append({
                'filename': file.filename,
                'content_type': file.content_type,
                'size': file.size,
                'width': width,
                'height': height,
                's3_key_thumbnail': s3_key_thumbnail
            })

        # 원본 파일 업로드
        file_urls = await upload_files_to_s3(files)
        
        # 파일 정보를 DB에 저장
        uploaded_files = []
        for file_url, metadata in zip(file_urls, file_metadata_list):
            # URL에서 s3_key만 추출
            s3_key = extract_s3_key_from_url(file_url)

            file_info = FileModel(
                file_name=metadata['filename'],
                s3_key=s3_key,
                s3_key_thumbnail=metadata['s3_key_thumbnail'],
                content_type=metadata['content_type'],
                file_size=metadata['size'],
                width=metadata['width'],
                height=metadata['height']
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