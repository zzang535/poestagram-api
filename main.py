from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import test, email

app = FastAPI(
    title="Poe2stagram API",
    description="Poe2stagram API 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(test.router, prefix="/api/v1", tags=["test"])
app.include_router(email.router, prefix="/api/v1", tags=["email"])

@app.get("/")
async def root():
    return {"message": "Welcome to Poe2stagram API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 