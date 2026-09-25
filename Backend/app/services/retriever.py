from typing import List, Dict, Any, Optional

from sentence_transformers import CrossEncoder
from functools import lru_cache

from app.config import settings
from app.services.vector_store import similarity_search


@lru_cache()
def get_reranker() -> CrossEncoder:
    """Cross-encoder reranker, loaded once and cached."""
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def retrieve(
    query: str, document_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Vector similarity search -> top_k candidates."""
    return similarity_search(query, top_k=settings.TOP_K, document_ids=document_ids)


def rerank(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rerank candidates with a cross-encoder and keep the top N."""
    if not candidates:
        return []

    model = get_reranker()
    pairs = [(query, c["content"]) for c in candidates]
    scores = model.predict(pairs)

    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)

    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[: settings.RERANK_TOP_N]


def retrieve_and_rerank(
    query: str, document_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    candidates = retrieve(query, document_ids=document_ids)
    return rerank(query, candidates)