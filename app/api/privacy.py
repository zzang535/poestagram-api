from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.base import get_db
from app.crud import privacy as privacy_crud
from app.schemas.privacy import Privacy, PrivacyCreate, PrivacyUpdate

router = APIRouter()

@router.get("/", response_model=Privacy)
def get_latest_privacy(db: Session = Depends(get_db)):
    privacy = privacy_crud.get_latest_privacy(db)
    if not privacy:
        raise HTTPException(status_code=404, detail="Privacy policy not found")
    return privacy

@router.get("/{privacy_id}", response_model=Privacy)
def get_privacy(privacy_id: int, db: Session = Depends(get_db)):
    privacy = privacy_crud.get_privacy(db, privacy_id)
    if not privacy:
        raise HTTPException(status_code=404, detail="Privacy policy not found")
    return privacy

@router.post("/", response_model=Privacy)
def create_privacy(privacy: PrivacyCreate, db: Session = Depends(get_db)):
    return privacy_crud.create_privacy(db, privacy)

@router.put("/{privacy_id}", response_model=Privacy)
def update_privacy(privacy_id: int, privacy: PrivacyUpdate, db: Session = Depends(get_db)):
    updated_privacy = privacy_crud.update_privacy(db, privacy_id, privacy)
    if not updated_privacy:
        raise HTTPException(status_code=404, detail="Privacy policy not found")
    return updated_privacy

@router.delete("/{privacy_id}")
def delete_privacy(privacy_id: int, db: Session = Depends(get_db)):
    success = privacy_crud.delete_privacy(db, privacy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Privacy policy not found")
    return {"message": "Privacy policy deleted successfully"} 