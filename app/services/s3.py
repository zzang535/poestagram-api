import boto3
import os
from fastapi import UploadFile
import logging
from typing import List
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

async def upload_file_to_s3(file: UploadFile, folder: str = "uploads") -> str:
    """
    단일 파일을 S3에 업로드하고 URL을 반환합니다.
    """
    try:
        # 파일명에 타임스탬프 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        s3_key = f"{folder}/{timestamp}_{file.filename}"
        
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

async def upload_files_to_s3(files: List[UploadFile], folder: str = "uploads") -> List[str]:
    """
    여러 파일을 S3에 업로드하고 URL 목록을 반환합니다.
    """
    file_urls = []
    
    for file in files:
        try:
            file_url = await upload_file_to_s3(file, folder)
            file_urls.append(file_url)
        except Exception as e:
            logger.error(f"파일 업로드 실패 ({file.filename}): {str(e)}")
            raise e
    
    return file_urls 