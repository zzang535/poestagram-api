# Poe2stagram API

FastAPI를 사용한 Poe2stagram API 서비스입니다.

## 설치 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 수정하여 필요한 환경 변수를 설정하세요
```

## 실행 방법

개발 서버 실행:
```bash
uvicorn main:app --reload
```

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
app/
├── api/            # API 라우터
├── core/           # 핵심 설정
├── models/         # 데이터베이스 모델
├── schemas/        # Pydantic 모델
└── services/       # 비즈니스 로직
``` 