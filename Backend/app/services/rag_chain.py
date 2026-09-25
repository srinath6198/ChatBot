import os
import time
from typing import List, Dict, Any, Optional, Tuple

from langchain_core.messages import SystemMessage, HumanMessage

from app.services.llm import get_llm
from app.services.retriever import retrieve_and_rerank

SYSTEM_PROMPT = """Answer using ONLY the provided document context. Be concise. \
Cite sources like [1], [2]. If the answer isn't in the context, say so."""


def _build_context(chunks: List[Dict[str, Any]]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        filename = c["metadata"].get("filename", "unknown")
        parts.append(f"[{i}] (source: {filename})\n{c['content']}")
    return "\n\n".join(parts)


def _get_tracer():
    """Optional Langfuse tracing handler; returns None if not configured."""
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return None
    try:
        from langfuse.callback import CallbackHandler

        return CallbackHandler()
    except Exception:
        return None


def answer_question(
    query: str, document_ids: Optional[List[str]] = None
) -> Tuple[str, List[Dict[str, Any]], int]:
    """
    Runs the full RAG pipeline: retrieve -> rerank -> generate.
    Returns (answer_text, source_chunks, latency_ms).
    """
    start = time.time()

    chunks = retrieve_and_rerank(query, document_ids=document_ids)
    context = _build_context(chunks)

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            if context
            else f"Question: {query}\n\n(No relevant context was found in the documents.)"
        ),
    ]

    callbacks = []
    tracer = _get_tracer()
    if tracer:
        callbacks.append(tracer)

    response = llm.invoke(messages, config={"callbacks": callbacks} if callbacks else {})
    latency_ms = int((time.time() - start) * 1000)

    return response.content, chunks, latency_ms