from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse
)
from app.crud import comment as comment_crud
from app.services.auth import get_current_user_id
from app.schemas.user import User

router = APIRouter()

