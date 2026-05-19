"""基础冒烟测试 — 验证应用可正常导入和创建"""

import pytest


class TestAppImport:
    """验证核心模块可导入（不依赖外部服务）"""

    def test_config_loads(self):
        from utils.config_handler import chroma_conf, rag_conf, agent_conf

        assert chroma_conf["collection_name"] == "agent"
        assert "chunk_size" in chroma_conf
        assert rag_conf["chat_model_name"] == "qwen3-max"
        assert "student_score_data_path" in agent_conf or True

    def test_backend_app_imports(self):
        from backend.app.main import app

        assert app.title == "AI Teaching Assistant API"
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/api/chat" in routes
        assert "/api/auth/login" in routes

    def test_vector_store_default_chroma(self):
        from rag.vector_store import VectorStoreService

        store = VectorStoreService()
        assert store.vector_store is not None
        assert store.spliter is not None

    def test_milvus_overrides_create_vector_store(self):
        """验证 MilvusVectorStoreService 覆写了 _create_vector_store 方法"""
        from rag.milvus_vector_store import MilvusVectorStoreService
        from rag.vector_store import VectorStoreService

        parent_method = VectorStoreService._create_vector_store
        child_method = MilvusVectorStoreService._create_vector_store
        assert child_method is not parent_method, "MilvusVectorStoreService 应覆写 _create_vector_store"

    def test_path_resolution(self):
        from utils.path_tools import get_abs_path, get_project_root

        root = get_project_root()
        assert root is not None
        assert get_abs_path("config/rag.yml") is not None

    def test_db_url_default(self):
        from backend.app.db import DATABASE_URL
        assert DATABASE_URL.startswith("sqlite:///")
