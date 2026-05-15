from __future__ import annotations

from functools import lru_cache
import os

from backend.app.core import runtime  # noqa: F401
from agent.react_agent import ReactAgent
from rag.milvus_vector_store import MilvusVectorStoreService
from rag.vector_store import VectorStoreService


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreService:
    backend = os.getenv("VECTOR_BACKEND", "chroma").strip().lower()
    if backend == "milvus":
        store = MilvusVectorStoreService()
    else:
        store = VectorStoreService()
    store.load_document()
    return store


@lru_cache(maxsize=1)
def get_agent() -> ReactAgent:
    get_vector_store()
    return ReactAgent()
