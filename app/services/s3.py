import boto3
import os
from fastapi import UploadFile
import logging
from typing import List
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

def get_s3_prefix(content_type: str) -> str:
    """
    콘텐츠 타입에 따라 S3 프리픽스를 반환합니다.
    
    Args:
        content_type: 파일의 MIME 타입
        
    Returns:
        str: S3 프리픽스 (예: "poestagram/images", "poestagram/videos")
    """
    if content_type and content_type.startswith('image/'):
        return "poestagram/images"
    elif content_type and content_type.startswith('video/'):
        return "poestagram/videos"
    else:
        # 기본값 (알 수 없는 타입)
        return "poestagram/files"

async def upload_file_to_s3(file: UploadFile) -> str:
    """
    단일 파일을 S3에 업로드하고 URL을 반환합니다.
    콘텐츠 타입에 따라 자동으로 프리픽스를 설정합니다.
    """
    try:
        # 콘텐츠 타입에 따른 프리픽스 결정
        prefix = get_s3_prefix(file.content_type)
        
        # 파일명에 타임스탬프 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        s3_key = f"{prefix}/{timestamp}_{file.filename}"
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        # 업로드된 파일의 URL 생성
        file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
        
        logger.info(f"파일 업로드 성공: {s3_key}")
        return file_url
        
    except Exception as e:
        logger.error(f"파일 업로드 실패: {str(e)}")
        raise Exception(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")

async def upload_files_to_s3(files: List[UploadFile]) -> List[str]:
    """
    여러 파일을 S3에 업로드하고 URL 목록을 반환합니다.
    각 파일의 콘텐츠 타입에 따라 자동으로 프리픽스를 설정합니다.
    """
    file_urls = []
    
    for file in files:
        try:
            file_url = await upload_file_to_s3(file)
            file_urls.append(file_url)
        except Exception as e:
            logger.error(f"파일 업로드 실패 ({file.filename}): {str(e)}")
            raise e
    
    return file_urls

def delete_file_from_s3(s3_key: str) -> bool:
    """
    S3에서 파일을 삭제합니다.
    
    Args:
        s3_key: 삭제할 파일의 S3 키 (예: "poestagram/images/20231201_120000_image.jpg")
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=s3_key
        )
        logger.info(f"S3 파일 삭제 성공: {s3_key}")
        return True
    except Exception as e:
        logger.error(f"S3 파일 삭제 실패 ({s3_key}): {str(e)}")
        return False 