import os
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import settings


def extract_text(file_path: str) -> str:
    """Extract raw text from a supported document (.pdf, .txt, .md)."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    if ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str) -> List[str]:
    """Split extracted text into overlapping chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]


def process_document(file_path: str) -> List[str]:
    """Full pipeline: extract -> chunk. Returns list of chunk strings."""
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError("No extractable text found in document")
    return chunk_text(text)