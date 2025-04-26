import logging
import re
from PIL import Image
import io
from moviepy.editor import VideoFileClip
import tempfile
import os
from fastapi import UploadFile
import cv2
import numpy as np
from tempfile import SpooledTemporaryFile

logger = logging.getLogger(__name__)

def split_file_url(file_url: str) -> tuple:
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

async def get_video_dimensions(file: UploadFile) -> tuple:
    """
    비디오 파일의 크기 정보를 반환합니다.
    """
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # 파일 내용을 임시 파일에 저장
            contents = await file.read()
            temp_file.write(contents)
            temp_file.flush()
            
            # 비디오 파일 로드
            video = VideoFileClip(temp_file.name)
            width, height = video.size
            
            # 임시 파일 삭제
            os.unlink(temp_file.name)
            
            return width, height
    except Exception as e:
        logger.warning(f"비디오 크기 확인 중 오류 발생: {str(e)}")
        return None, None
    finally:
        # 파일 포인터를 처음 위치로 되돌림
        await file.seek(0)

async def extract_video_thumbnail(file: UploadFile) -> UploadFile:
    """
    비디오 파일에서 썸네일을 추출합니다.
    """
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file.flush()
            
            # 비디오 파일 로드
            video = VideoFileClip(temp_file.name)
            
            # 비디오 중간 지점의 프레임 추출
            thumbnail_frame = video.get_frame(video.duration / 2)
            
            # RGB to BGR 변환 (OpenCV 형식)
            thumbnail_frame_bgr = cv2.cvtColor(thumbnail_frame, cv2.COLOR_RGB2BGR)
            
            # 썸네일 저장
            thumbnail_path = f"{temp_file.name}_thumbnail.jpg"
            cv2.imwrite(thumbnail_path, thumbnail_frame_bgr)
            
            # 비디오 파일 닫기 및 삭제
            video.close()
            os.unlink(temp_file.name)
            
            # 썸네일 파일을 SpooledTemporaryFile로 읽기
            spooled_file = SpooledTemporaryFile()
            with open(thumbnail_path, 'rb') as f:
                spooled_file.write(f.read())
            spooled_file.seek(0)
            
            # 썸네일 파일을 UploadFile로 변환
            thumbnail_filename = f"{os.path.splitext(file.filename)[0]}_thumbnail.jpg"
            thumbnail = UploadFile(
                filename=thumbnail_filename,
                file=spooled_file,
                headers={"content-type": "image/jpeg"}
            )
            
            # 임시 썸네일 파일 삭제
            os.unlink(thumbnail_path)
            
            # 원본 파일 포인터 위치 복구
            await file.seek(0)
            
            return thumbnail
            
    except Exception as e:
        logger.error(f"비디오 썸네일 추출 중 오류 발생: {str(e)}")
        return None
    finally:
        await file.seek(0) 