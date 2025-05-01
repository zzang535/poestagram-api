from fastapi import APIRouter, File as FastAPIFile, UploadFile, HTTPException
from typing import List
from app.schemas.file import FileUploadResponse, File
from app.services.s3 import upload_files_to_s3
from app.services.media import split_file_url, get_image_dimensions, get_video_dimensions, extract_video_thumbnail, get_video_rotation
from app.models.file import File as FileModel
from app.db.base import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

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
                    # 1. 너비, 높이 가져오기
                    width, height = await get_video_dimensions(file)
                    # 2. 회전 정보 가져오기
                    rotation = await get_video_rotation(file)

                    # 3. 회전 정보에 따라 최종 width, height 결정
                    if width is not None and height is not None:
                        logger.info(f"원본 비디오 크기: {width}x{height}, 회전: {rotation}도")
                        if rotation in (90, 270): # 세로 영상
                            logger.info(f"세로 영상 감지. width와 height를 교환합니다.")
                            width, height = height, width
                        else:
                             logger.info(f"가로 영상 또는 회전 정보 없음.")
                    else:
                         logger.warning(f"비디오 크기 정보를 가져올 수 없습니다: {file.filename}")

                    # 비디오 썸네일 추출 및 업로드
                    thumbnail = await extract_video_thumbnail(file)
                    if thumbnail:
                        try:
                            thumbnail_urls = await upload_files_to_s3([thumbnail])
                            if thumbnail_urls:
                                _, s3_key_thumbnail = split_file_url(thumbnail_urls[0])
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
            # URL을 base_url과 s3_key로 분리
            base_url, s3_key = split_file_url(file_url)

            file_info = FileModel(
                file_name=metadata['filename'],
                base_url=base_url,
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