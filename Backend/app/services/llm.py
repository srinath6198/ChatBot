from functools import lru_cache

from langchain_ollama import ChatOllama

from app.config import settings


@lru_cache()
def get_llm() -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.2,
        num_predict=512,
        num_ctx=2048,
    )