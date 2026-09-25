from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_admin
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=schemas.SystemStats)
def system_stats(
    current_admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return schemas.SystemStats(
        total_users=db.query(models.User).count(),
        total_documents=db.query(models.Document).count(),
        total_chunks=db.query(models.DocumentChunk).count(),
        total_chat_sessions=db.query(models.ChatSession).count(),
        total_messages=db.query(models.ChatMessage).count(),
    )


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(
    current_admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.patch("/users/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: str,
    payload: schemas.UserRoleUpdate,
    current_admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=schemas.UserOut)
def deactivate_user(
    user_id: str,
    current_admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.get("/documents", response_model=list[schemas.DocumentOut])
def all_documents(
    current_admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.Document).order_by(models.Document.created_at.desc()).all()