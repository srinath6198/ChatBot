import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.services.document_processor import process_document
from app.services.vector_store import add_chunks, delete_document_chunks

router = APIRouter(prefix="/documents", tags=["documents"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _ingest_document(document_id: str, db: Session) -> None:
    """Background task: extract -> chunk -> embed -> store."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        return

    try:
        document.status = "processing"
        db.commit()

        chunks = process_document(document.file_path)

        chunk_records = []
        chunk_ids = []
        texts = []
        metadatas = []

        for idx, chunk_text in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_records.append(
                models.DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=idx,
                    content=chunk_text,
                    vector_id=chunk_id,
                )
            )
            chunk_ids.append(chunk_id)
            texts.append(chunk_text)
            metadatas.append(
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": idx,
                }
            )

        db.add_all(chunk_records)
        document.num_chunks = len(chunk_records)
        document.status = "chunked"
        db.commit()

        add_chunks(chunk_ids, texts, metadatas)

        document.status = "embedded"
        db.commit()

    except Exception as exc:  # noqa: BLE001
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()


@router.post("/upload", response_model=schemas.DocumentOut, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    doc_id = str(uuid.uuid4())
    saved_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{ext}")

    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    with open(saved_path, "wb") as f:
        f.write(contents)

    document = models.Document(
        id=doc_id,
        owner_id=current_user.id,
        filename=file.filename,
        file_path=saved_path,
        file_size_bytes=len(contents),
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(_ingest_document, document.id, db)

    return document


@router.get("", response_model=schemas.DocumentListResponse)
def list_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Document).filter(models.Document.owner_id == current_user.id)
    documents = query.order_by(models.Document.created_at.desc()).all()
    return schemas.DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(
    document_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.owner_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.owner_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document.id)

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    return None