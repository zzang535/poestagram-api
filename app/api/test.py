from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # 간단한 쿼리 실행
        result = db.execute(text("SELECT 1"))
        return {"status": "success", "message": "데이터베이스 연결 성공"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/test-table")
async def test_table(db: Session = Depends(get_db)):
    try:
        # users 테이블의 컬럼 정보 조회
        result = db.execute(text("DESCRIBE users"))
        columns = [row[0] for row in result]
        return {"status": "success", "columns": columns}
    except Exception as e:
        return {"status": "error", "message": str(e)} 