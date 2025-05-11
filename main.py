from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, privacy, test, file, feed, users, comment
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Poestagram API",
    description="Poestagram API 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용하도록 설정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(privacy.router, prefix="/api/privacy", tags=["privacy"])
app.include_router(test.router, prefix="/api/test", tags=["test"])
app.include_router(file.router, prefix="/api/files", tags=["files"])
app.include_router(feed.router, prefix="/api", tags=["feeds"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(comment.router, prefix="/api", tags=["comments"])

@app.get("/")
async def root():
    return {"message": "Welcome to Poestagram API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 