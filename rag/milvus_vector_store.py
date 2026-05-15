from __future__ import annotations

import os

from langchain_milvus import Milvus

from model.factory import embed_model
from rag.vector_store import VectorStoreService
from utils.config_handler import chroma_conf


class MilvusVectorStoreService(VectorStoreService):
    """
    复用现有 VectorStoreService 的业务逻辑（切分、去重、引用追踪、删除、重置），
    仅替换底层向量库实现为 Milvus。
    """

    def __init__(self):
        super().__init__()

        milvus_uri = os.getenv("MILVUS_URI", "http://127.0.0.1:19530")
        milvus_collection = os.getenv("MILVUS_COLLECTION", chroma_conf["collection_name"])

        self.vector_store = Milvus(
            embedding_function=embed_model,
            connection_args={"uri": milvus_uri},
            collection_name=milvus_collection,
            auto_id=False,
            drop_old=False,
        )
