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
import subprocess
import json

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
    비디오 파일의 width, height를 반환합니다. (회전 고려하지 않음)
    """
    width, height = None, None
    temp_filename = None
    try:
        # 임시 파일 생성 및 내용 쓰기
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file.flush()
            temp_filename = temp_file.name
        
        # moviepy로 비디오 로드 및 크기 가져오기
        video = VideoFileClip(temp_filename)
        width, height = video.size
        video.close() # 리소스 해제
        
        return width, height
    except Exception as e:
        logger.warning(f"비디오 크기 확인 중 오류 발생 (moviepy): {str(e)}")
        return None, None # 오류 발생 시 None 반환
    finally:
        # 임시 파일 삭제 및 파일 포인터 복구
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as e:
                 logger.error(f"임시 파일 삭제 중 오류 발생: {str(e)}")
        await file.seek(0)

async def get_video_rotation(file: UploadFile) -> int:
    """
    비디오 파일의 회전 정보를 반환합니다. (ffprobe 사용, 없으면 0 반환)
    """
    rotation = 0
    temp_filename = None
    try:
        # 임시 파일 생성 및 내용 쓰기
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file.flush()
            temp_filename = temp_file.name

        # ffprobe 명령 실행 준비
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream_side_data=rotation', # stream_tags=rotate 대신 side_data 사용 시도
            '-of', 'json',
            temp_filename
        ]
        
        logger.info(f"Executing ffprobe command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            logger.warning(f"ffprobe 실행 오류 (stderr): {result.stderr}")
            # stream_tags=rotate 로 재시도
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream_tags=rotate',
                '-of', 'json',
                temp_filename
            ]
            logger.info(f"Retrying ffprobe command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                 logger.warning(f"ffprobe 재시도 오류 (stderr): {result.stderr}")
                 return 0 # 두 번 모두 실패 시 0 반환

        output = result.stdout
        logger.info(f"ffprobe output: {output}")

        # ffprobe 출력 파싱
        try:
            ffprobe_data = json.loads(output)
            parsed_rotation = 0 # 파싱된 rotation 임시 저장
            if 'streams' in ffprobe_data and ffprobe_data['streams']:
                stream = ffprobe_data['streams'][0]
                # side_data 확인 (side_data_type 체크 없이 rotation 키 확인)
                if 'side_data_list' in stream:
                    for side_data in stream['side_data_list']:
                        if 'rotation' in side_data:
                            try:
                                parsed_rotation = int(side_data['rotation'])
                                logger.info(f"Rotation found in side_data_list: {parsed_rotation}")
                                break # 첫 번째 rotation 값 사용
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid rotation value in side_data: {side_data['rotation']}")
                                
                # side_data에 없으면 tags 확인
                if parsed_rotation == 0 and 'tags' in stream: # side_data에서 못 찾았을 경우만 tags 확인
                     try:
                         parsed_rotation = int(stream['tags'].get('rotate', 0))
                         if parsed_rotation != 0:
                             logger.info(f"Rotation found in tags: {parsed_rotation}")
                     except (ValueError, TypeError):
                         logger.warning(f"Invalid rotation value in tags: {stream['tags'].get('rotate')}")
                         parsed_rotation = 0
            
            # 최종 rotation 값 설정 및 음수 처리
            rotation = parsed_rotation
            if rotation < 0:
                rotation += 360
                
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"ffprobe 출력 파싱 오류: {str(e)}, output: {output}")
            rotation = 0 # 파싱 실패 시 0 반환

        return rotation
    except Exception as e:
        logger.error(f"비디오 회전 정보 확인 중 오류 발생: {str(e)}")
        return 0 # 그 외 예외 발생 시 0 반환
    finally:
        # 임시 파일 삭제 및 파일 포인터 복구
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as e:
                 logger.error(f"임시 파일 삭제 중 오류 발생: {str(e)}")
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