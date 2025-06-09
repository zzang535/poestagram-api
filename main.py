from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, test, file, feed, users, comment
import logging
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 정보 출력 함수
def print_database_info():
    try:
        from app.core.config import settings
        from app.db.base import get_db
        from sqlalchemy import text
        
        print("\n" + "="*60)
        print("🚀 POESTAGRAM API 서버 시작")
        print("="*60)
        print(f"📊 DATABASE_URL: {settings.DATABASE_URL}")
        
        # 실제 연결된 데이터베이스 확인
        db = next(get_db())
        result = db.execute(text("SELECT DATABASE() as current_db"))
        current_db = result.fetchone()[0]
        print(f"🎯 현재 연결된 데이터베이스: {current_db}")
        
        # 테이블 개수 확인
        tables_result = db.execute(text("SHOW TABLES"))
        table_count = len(tables_result.fetchall())
        print(f"📋 테이블 개수: {table_count}")
        
        db.close()
        print("="*60)
        print()
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 확인 중 오류 발생: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    print_database_info()
    yield
    # 서버 종료 시 실행 (필요한 경우)

app = FastAPI(
    title="Poestagram API",
    description="Poestagram API 서비스",
    version="1.0.0",
    lifespan=lifespan
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
app.include_router(test.router, prefix="/api/test", tags=["test"])
app.include_router(file.router, prefix="/api/files", tags=["files"])
app.include_router(feed.router, prefix="/api/feeds", tags=["feeds"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(comment.router, prefix="/api/comments", tags=["comments"])

@app.get("/")
async def root():
    return {"message": "Welcome to Poestagram API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 