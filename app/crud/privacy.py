from sqlalchemy.orm import Session
from app.models.privacy import Privacy
from app.schemas.privacy import PrivacyCreate, PrivacyUpdate

def get_privacy(db: Session, privacy_id: int):
    return db.query(Privacy).filter(Privacy.id == privacy_id).first()

def get_latest_privacy(db: Session):
    return db.query(Privacy).order_by(Privacy.effective_date.desc()).first()

def create_privacy(db: Session, privacy: PrivacyCreate):
    db_privacy = Privacy(**privacy.model_dump())
    db.add(db_privacy)
    db.commit()
    db.refresh(db_privacy)
    return db_privacy

def update_privacy(db: Session, privacy_id: int, privacy: PrivacyUpdate):
    db_privacy = db.query(Privacy).filter(Privacy.id == privacy_id).first()
    if db_privacy:
        for key, value in privacy.model_dump().items():
            setattr(db_privacy, key, value)
        db.commit()
        db.refresh(db_privacy)
    return db_privacy

def delete_privacy(db: Session, privacy_id: int):
    db_privacy = db.query(Privacy).filter(Privacy.id == privacy_id).first()
    if db_privacy:
        db.delete(db_privacy)
        db.commit()
        return True
    return False 