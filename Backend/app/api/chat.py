import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.services.rag_chain import answer_question
from app.services.retriever import retrieve_and_rerank
from app.services.llm import get_llm
from app.services.rag_chain import SYSTEM_PROMPT, _build_context
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=schemas.ChatSessionOut, status_code=201)
def create_session(
    payload: schemas.ChatSessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = models.ChatSession(user_id=current_user.id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[schemas.ChatSessionOut])
def list_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.created_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}/messages", response_model=list[schemas.ChatMessageOut])
def get_messages(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(session_id, current_user, db)
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )

    out = []
    for m in messages:
        sources = json.loads(m.sources) if m.sources else None
        out.append(
            schemas.ChatMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=sources,
                latency_ms=m.latency_ms,
                created_at=m.created_at,
            )
        )
    return out


@router.post("/message", response_model=schemas.ChatResponse)
def send_message(
    payload: schemas.ChatMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(payload.session_id, current_user, db)

    # Save user message
    user_msg = models.ChatMessage(
        session_id=session.id, role="user", content=payload.message
    )
    db.add(user_msg)
    db.commit()

    # Run RAG pipeline
    try:
        answer_text, chunks, latency_ms = answer_question(
            payload.message, document_ids=payload.document_ids
        )
    except Exception as e:
        # Delete the user message since we couldn't generate a response
        db.delete(user_msg)
        db.commit()
        error_message = str(e)
        lowered_error = error_message.lower()
        if (
            "11434" in lowered_error
            or "ollama" in lowered_error
            or "connection refused" in lowered_error
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Ollama is unavailable. Start Ollama and make sure the "
                    f"'{settings.OLLAMA_MODEL}' model is installed, then try again."
                ),
            )
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {error_message}")

    sources = [
        schemas.SourceChunk(
            document_id=c["metadata"]["document_id"],
            filename=c["metadata"]["filename"],
            chunk_index=c["metadata"]["chunk_index"],
            content=c["content"],
            score=c.get("rerank_score", c.get("score", 0.0)),
        )
        for c in chunks
    ]

    assistant_msg = models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        sources=json.dumps([s.model_dump() for s in sources]),
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return schemas.ChatResponse(
        session_id=session.id,
        message=schemas.ChatMessageOut(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            sources=sources,
            latency_ms=assistant_msg.latency_ms,
            created_at=assistant_msg.created_at,
        ),
    )


@router.post("/stream")
def stream_message(
    payload: schemas.ChatMessageCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(payload.session_id, current_user, db)

    user_msg = models.ChatMessage(
        session_id=session.id, role="user", content=payload.message
    )
    db.add(user_msg)
    db.commit()

    try:
        chunks = retrieve_and_rerank(payload.message, document_ids=payload.document_ids)
    except Exception as e:
        db.delete(user_msg)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Retrieval error: {e}")

    context = _build_context(chunks)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Context:\n{context}\n\nQuestion: {payload.message}\n\nAnswer:"
            if context
            else f"Question: {payload.message}\n\n(No relevant context was found.)"
        ),
    ]
    sources = [
        schemas.SourceChunk(
            document_id=c["metadata"]["document_id"],
            filename=c["metadata"]["filename"],
            chunk_index=c["metadata"]["chunk_index"],
            content=c["content"],
            score=c.get("rerank_score", c.get("score", 0.0)),
        )
        for c in chunks
    ]

    def generate():
        llm = get_llm()
        start = time.time()
        full_text = ""
        for token in llm.stream(messages):
            full_text += token.content
            yield token.content

        latency_ms = int((time.time() - start) * 1000)
        assistant_msg = models.ChatMessage(
            session_id=session.id,
            role="assistant",
            content=full_text,
            sources=json.dumps([s.model_dump() for s in sources]),
            latency_ms=latency_ms,
        )
        db.add(assistant_msg)
        db.commit()

        # Send sources as final JSON line
        yield f"\n__SOURCES__{json.dumps([s.model_dump() for s in sources])}__END__"

    return StreamingResponse(generate(), media_type="text/plain")


def _get_owned_session(
    session_id: str, current_user: models.User, db: Session
) -> models.ChatSession:
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session