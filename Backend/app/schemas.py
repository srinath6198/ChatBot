from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Documents ----------

class DocumentOut(BaseModel):
    id: str
    filename: str
    status: str
    num_chunks: int
    file_size_bytes: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentOut]
    total: int


# ---------- Chat ----------

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    session_id: str
    message: str
    document_ids: Optional[List[str]] = None  # restrict retrieval to these docs


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[SourceChunk]] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: ChatMessageOut
    session_id: str


# ---------- Admin ----------

class SystemStats(BaseModel):
    total_users: int
    total_documents: int
    total_chunks: int
    total_chat_sessions: int
    total_messages: int


class UserRoleUpdate(BaseModel):
    role: str