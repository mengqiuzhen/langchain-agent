"""基础冒烟测试 — 验证核心模块可正常导入和创建"""

import pytest


class TestAppImport:
    """验证核心模块可导入（不依赖外部服务）"""

    def test_config_loads(self):
        from utils.config_handler import rag_conf, chroma_conf, agent_conf

        assert rag_conf["chat_model_name"] == "qwen3-max"
        assert "collection_name" in chroma_conf
        assert chroma_conf["persist_directory"] == "chroma_db"

    def test_path_resolution(self):
        from utils.path_tools import get_abs_path, get_project_root

        root = get_project_root()
        abs_path = get_abs_path("config/rag.yml")
        assert abs_path.endswith("config/rag.yml")
        assert root in abs_path

    def test_app_imports(self):
        from backend.app.main import app

        assert app.title == "AI Teaching Assistant API"
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/api/chat" in routes

    def test_db_module(self):
        from backend.app.db import DATABASE_URL, engine

        assert "sqlite" in DATABASE_URL
        assert engine is not None

    def test_vector_store_creates_without_error(self):
        from rag.vector_store import VectorStoreService

        store = VectorStoreService()
        assert store.vector_store is not None

    def test_milvus_vector_store_uses_correct_impl(self):
        from rag.milvus_vector_store import MilvusVectorStoreService
        from langchain_milvus import Milvus

        store = MilvusVectorStoreService()
        assert isinstance(store.vector_store, Milvus)

    def test_agent_tools_load(self):
        from agent.tools.agent_tools import rag_summarize, query_student_scores

        assert rag_summarize.name is not None
        assert query_student_scores.name is not None


@pytest.mark.asyncio
class TestAsync:
    async def test_react_agent_creates(self):
        from agent.react_agent import ReactAgent

        agent = ReactAgent()
        assert agent.agent is not None
