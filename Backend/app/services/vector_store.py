from functools import lru_cache
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.embeddings import embed_texts, embed_query


@lru_cache()
def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    chunk_ids: List[str],
    texts: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """Embed chunk texts and upsert them into the Chroma collection."""
    embeddings = embed_texts(texts)
    collection = get_collection()
    collection.upsert(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def similarity_search(
    query: str, top_k: int, document_ids: List[str] | None = None
) -> List[Dict[str, Any]]:
    """Return top_k most similar chunks to the query, optionally scoped to document_ids."""
    collection = get_collection()
    query_embedding = embed_query(query)

    where = {"document_id": {"$in": document_ids}} if document_ids else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    hits = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for i in range(len(ids)):
        # Chroma cosine distance -> similarity score
        score = 1 - dists[i] if dists[i] is not None else 0.0
        hits.append(
            {
                "chunk_id": ids[i],
                "content": docs[i],
                "metadata": metas[i],
                "score": score,
            }
        )
    return hits


def delete_document_chunks(document_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"document_id": document_id})