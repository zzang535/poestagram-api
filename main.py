from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, privacy, test

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
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(privacy.router, prefix="/api", tags=["privacy"])
app.include_router(test.router, prefix="/api", tags=["test"])

@app.get("/")
async def root():
    return {"message": "Welcome to Poestagram API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 