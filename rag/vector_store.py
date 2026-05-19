import hashlib
import json
import os
import re
import tempfile
from typing import Optional


from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model.factory import embed_model
from utils.config_handler import chroma_conf
from utils.file_handler import csv_loader, get_file_md5_hex, listdir_with_allowed_type, pdf_loader, txt_loader
from utils.logger_handler import logger
from utils.path_tools import get_abs_path


class VectorStoreService:
    def __init__(self):
        self._init_common()
        self.vector_store = self._create_vector_store()

    def _init_common(self):
        """共享初始化：分片器 + 引用追踪路径"""
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )
        self.chunk_ref_store_path = get_abs_path("logs/chunk_refs.json")
        self.file_ref_store_path = get_abs_path("logs/file_refs.json")

    def _create_vector_store(self):
        """创建底层向量库实例（子类可覆写）"""
        return Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"]),
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def similarity_search_with_score(self, query: str, k: Optional[int] = None, filter_dict: Optional[dict] = None):
        top_k = k if k is not None else chroma_conf["k"]
        try:
            return self.vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
        except TypeError:
            # 兼容 Milvus 等不支持 filter 参数的向量后端
            return self.vector_store.similarity_search_with_score(query, k=top_k)

    @staticmethod
    def _normalize_chunk_text(text: str) -> str:
        text = (text or "").strip()
        return re.sub(r"\s+", " ", text)

    def _chunk_hash(self, text: str) -> str:
        normalized = self._normalize_chunk_text(text)
        return hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()

    @staticmethod
    def _ensure_parent(path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _load_json_dict(self, path: str) -> dict:
        if not os.path.exists(path):
            self._ensure_parent(path)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_json_dict(self, path: str, data: dict):
        self._ensure_parent(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_chunk_refs(self) -> dict:
        return self._load_json_dict(self.chunk_ref_store_path)

    def _save_chunk_refs(self, data: dict):
        self._save_json_dict(self.chunk_ref_store_path, data)

    def _load_file_refs(self) -> dict:
        return self._load_json_dict(self.file_ref_store_path)

    def _save_file_refs(self, data: dict):
        self._save_json_dict(self.file_ref_store_path, data)

    def _check_md5_hex(self, md5_for_check: str) -> bool:
        md5_store_path = get_abs_path(chroma_conf["md5_hex_store"])
        if not os.path.exists(md5_store_path):
            open(md5_store_path, "w", encoding="utf-8").close()
            return False

        with open(md5_store_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip() == md5_for_check:
                    return True
        return False

    def _save_md5_hex(self, md5_for_save: str):
        with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
            f.write(md5_for_save + "\n")

    def _remove_md5_hex(self, md5_for_remove: str):
        path = get_abs_path(chroma_conf["md5_hex_store"])
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        kept = [line for line in lines if line != md5_for_remove]
        with open(path, "w", encoding="utf-8") as f:
            for line in kept:
                f.write(line + "\n")

    @staticmethod
    def _get_file_documents(read_path: str):
        if read_path.endswith("txt"):
            return txt_loader(read_path)
        if read_path.endswith("pdf"):
            return pdf_loader(read_path)
        if read_path.endswith("csv"):
            return csv_loader(read_path)
        return []

    @staticmethod
    def _normalize_metadata(base_metadata: Optional[dict]) -> dict:
        metadata = base_metadata or {}
        return {
            "source": metadata.get("source", "未知来源"),
            "subject": metadata.get("subject", "未分类"),
            "grade": metadata.get("grade", "未分类"),
            "author": metadata.get("author", "未分类"),
            "file_md5": metadata.get("file_md5", ""),
        }

    @staticmethod
    def _merge_metadata(documents: list[Document], base_metadata: dict) -> list[Document]:
        merged_docs = []
        for doc in documents:
            meta = dict(doc.metadata) if doc.metadata else {}
            meta.update(base_metadata)
            merged_docs.append(Document(page_content=doc.page_content, metadata=meta))
        return merged_docs

    @staticmethod
    def _is_structured_heading(line: str) -> bool:
        text = (line or "").strip()
        if not text or len(text) > 80:
            return False

        heading_patterns = [
            r"^第[一二三四五六七八九十百千\d]+[章节部分篇]\s*.*$",
            r"^[一二三四五六七八九十]+[、.．]\s*.+$",
            r"^\d+(\.\d+){0,3}\s+.+$",
            r"^\(?[一二三四五六七八九十\d]+\)?\s*.+$",
            r"^【[^】]{1,30}】$",
        ]
        return any(re.match(p, text) for p in heading_patterns)

    def _structured_split_documents(self, documents: list[Document]) -> list[Document]:
        """
        结构化优先切分：
        1) 先按“标题行 + 段落块”组织
        2) 对超长块再走递归切分（兜底），保持 overlap
        """
        structured_chunks: list[Document] = []
        chunk_size = int(chroma_conf["chunk_size"])

        for doc in documents:
            raw_text = (doc.page_content or "").strip()
            if not raw_text:
                continue

            lines = [ln.rstrip() for ln in raw_text.splitlines()]
            current_title = ""
            current_block_lines: list[str] = []

            def flush_block():
                nonlocal current_block_lines
                content = "\n".join([x for x in current_block_lines if x.strip()]).strip()
                if not content:
                    current_block_lines = []
                    return

                if current_title and not content.startswith(current_title):
                    content = f"{current_title}\n{content}"

                metadata = dict(doc.metadata) if doc.metadata else {}
                if current_title:
                    metadata["section_title"] = current_title
                structured_chunks.append(Document(page_content=content, metadata=metadata))
                current_block_lines = []

            for line in lines:
                stripped = line.strip()
                if self._is_structured_heading(stripped):
                    flush_block()
                    current_title = stripped
                    continue

                if not stripped:
                    flush_block()
                    continue

                current_block_lines.append(line)
                if len("\n".join(current_block_lines)) >= chunk_size:
                    flush_block()

            flush_block()

            if not structured_chunks:
                structured_chunks.append(Document(page_content=raw_text, metadata=dict(doc.metadata or {})))

        final_chunks: list[Document] = []
        for chunk in structured_chunks:
            normalized = self._normalize_chunk_text(chunk.page_content)
            if not normalized:
                continue

            if len(normalized) <= chunk_size:
                final_chunks.append(Document(page_content=normalized, metadata=dict(chunk.metadata or {})))
            else:
                fallback_parts = self.spliter.split_text(normalized)
                for part in fallback_parts:
                    part_norm = self._normalize_chunk_text(part)
                    if not part_norm:
                        continue
                    final_chunks.append(Document(page_content=part_norm, metadata=dict(chunk.metadata or {})))

        return final_chunks

    def add_documents(self, documents: list[Document], base_metadata: Optional[dict] = None) -> int:
        if not documents:
            return 0

        metadata = self._normalize_metadata(base_metadata)
        file_md5 = str(metadata.get("file_md5", "")).strip()
        if not file_md5:
            return 0

        with_meta = self._merge_metadata(documents, metadata)
        split_docs = self._structured_split_documents(with_meta)
        if not split_docs:
            return 0

        chunk_refs = self._load_chunk_refs()
        file_refs = self._load_file_refs()

        added_docs: list[Document] = []
        added_ids: list[str] = []
        file_chunk_hashes: list[str] = []

        for doc in split_docs:
            normalized_text = self._normalize_chunk_text(doc.page_content)
            if not normalized_text:
                continue

            chunk_hash = self._chunk_hash(normalized_text)
            file_chunk_hashes.append(chunk_hash)

            ref_item = chunk_refs.get(chunk_hash, {"ref_md5": []})
            ref_md5 = set(ref_item.get("ref_md5", []))
            if file_md5 not in ref_md5:
                ref_md5.add(file_md5)
                ref_item["ref_md5"] = sorted(ref_md5)
                chunk_refs[chunk_hash] = ref_item

            if len(ref_md5) == 1:
                doc.metadata = doc.metadata or {}
                doc.metadata["chunk_hash"] = chunk_hash
                added_docs.append(doc)
                added_ids.append(chunk_hash)

        # 创建或更新文件索引（即使新增分片数为0，也要记录该文件与共享chunk的关系）
        source = str(metadata.get("source", "未知来源")).strip() or "未知来源"
        file_refs[file_md5] = {
            "source": source,
            "subject": str(metadata.get("subject", "未分类")),
            "grade": str(metadata.get("grade", "未分类")),
            "author": str(metadata.get("author", "未分类")),
            "chunk_hashes": sorted(set(file_chunk_hashes)),
            "chunk_count": len(set(file_chunk_hashes)),
        }

        if added_docs:
            self.vector_store.add_documents(added_docs, ids=added_ids)

        self._save_chunk_refs(chunk_refs)
        self._save_file_refs(file_refs)
        return len(added_docs)

    def ingest_file(
        self,
        path: str,
        source_label: Optional[str] = None,
        skip_md5: bool = False,
        metadata: Optional[dict] = None,
    ) -> int:
        md5_hex = get_file_md5_hex(path)
        if not md5_hex:
            logger.warning(f"[加载知识库] {path} MD5计算失败，跳过")
            return 0

        if (not skip_md5) and self._check_md5_hex(md5_hex):
            logger.info(f"[加载知识库] {path} 内容已经存在于知识库，跳过")
            return 0

        documents: list[Document] = self._get_file_documents(path)
        if not documents:
            logger.warning(f"[加载知识库] {path} 无有效文本内容，跳过")
            return 0

        base_meta = dict(metadata or {})
        base_meta["source"] = source_label or os.path.basename(path)
        base_meta["file_md5"] = md5_hex

        count = self.add_documents(documents, base_metadata=base_meta)

        if not skip_md5:
            self._save_md5_hex(md5_hex)
        logger.info(f"[加载知识库] {path} 内容加载完成，新增唯一分片数: {count}")
        return count

    def ingest_uploaded_pdf_bytes_with_status(
        self, filename: str, data: bytes, metadata: Optional[dict] = None
    ) -> tuple[int, str]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            temp_path = tmp.name

        try:
            md5_hex = get_file_md5_hex(temp_path)
            if not md5_hex:
                return 0, "md5_failed"

            if self._check_md5_hex(md5_hex):
                return 0, "duplicate"

            documents: list[Document] = self._get_file_documents(temp_path)
            if not documents:
                return 0, "empty_content"

            base_meta = dict(metadata or {})
            base_meta["source"] = filename
            base_meta["file_md5"] = md5_hex
            count = self.add_documents(documents, base_metadata=base_meta)

            self._save_md5_hex(md5_hex)
            return count, "inserted"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def ingest_uploaded_pdf_bytes(self, filename: str, data: bytes, metadata: Optional[dict] = None) -> int:
        count, _ = self.ingest_uploaded_pdf_bytes_with_status(filename, data, metadata)
        return count

    @staticmethod
    def _build_where_filter(subject: str = "全部", grade: str = "全部", author: str = "全部") -> Optional[dict]:
        conditions = []
        if subject != "全部":
            conditions.append({"subject": {"$eq": subject}})
        if grade != "全部":
            conditions.append({"grade": {"$eq": grade}})
        if author != "全部":
            conditions.append({"author": {"$eq": author}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def search_with_filters(
        self,
        query: str,
        k: Optional[int] = None,
        subject: str = "全部",
        grade: str = "全部",
        author: str = "全部",
    ):
        filter_dict = self._build_where_filter(subject=subject, grade=grade, author=author)
        return self.similarity_search_with_score(query=query, k=k, filter_dict=filter_dict)

    def list_ingested_files(self) -> list[dict]:
        file_refs = self._load_file_refs()
        files = []
        for file_md5, info in file_refs.items():
            files.append(
                {
                    "source": str(info.get("source", "未知来源")),
                    "chunk_count": int(info.get("chunk_count", 0)),
                    "file_md5": file_md5,
                }
            )

        files.sort(key=lambda x: (-x["chunk_count"], x["source"]))
        return files

    def delete_by_source_or_md5(self, source: Optional[str] = None, file_md5: Optional[str] = None) -> dict:
        source = (source or "").strip()
        file_md5 = (file_md5 or "").strip()
        if not source and not file_md5:
            return {"deleted": False, "deleted_chunks": 0, "removed_md5": False}

        file_refs = self._load_file_refs()
        chunk_refs = self._load_chunk_refs()

        target_md5 = file_md5
        if not target_md5 and source:
            matched = [md5 for md5, info in file_refs.items() if str(info.get("source", "")).strip() == source]
            if len(matched) != 1:
                return {"deleted": False, "deleted_chunks": 0, "removed_md5": False}
            target_md5 = matched[0]

        if target_md5 not in file_refs:
            return {"deleted": False, "deleted_chunks": 0, "removed_md5": False}

        file_info = file_refs[target_md5]
        chunk_hashes = file_info.get("chunk_hashes", []) if isinstance(file_info, dict) else []
        deleted_chunks = 0

        for chunk_hash in chunk_hashes:
            item = chunk_refs.get(chunk_hash)
            if not item:
                continue
            refs = set(item.get("ref_md5", []))
            refs.discard(target_md5)

            if refs:
                item["ref_md5"] = sorted(refs)
                chunk_refs[chunk_hash] = item
            else:
                try:
                    self.vector_store.delete(ids=[chunk_hash])
                    deleted_chunks += 1
                except Exception:
                    pass
                chunk_refs.pop(chunk_hash, None)

        file_refs.pop(target_md5, None)
        self._save_file_refs(file_refs)
        self._save_chunk_refs(chunk_refs)
        self._remove_md5_hex(target_md5)

        return {"deleted": True, "deleted_chunks": deleted_chunks, "removed_md5": True}

    def reset_store(self) -> dict:
        """
        重置知识库相关数据：
        - 清空向量库 collection
        - 清空文件/分片引用索引
        - 清空 md5 去重文件
        返回重置统计信息
        """
        deleted_vectors = 0

        try:
            records = self.vector_store.get(include=[])
            ids = records.get("ids", []) if records else []
            if ids:
                self.vector_store.delete(ids=ids)
                deleted_vectors = len(ids)
        except Exception:
            deleted_vectors = 0

        self._save_chunk_refs({})
        self._save_file_refs({})

        md5_path = get_abs_path(chroma_conf["md5_hex_store"])
        os.makedirs(os.path.dirname(md5_path), exist_ok=True)
        with open(md5_path, "w", encoding="utf-8") as f:
            f.write("")

        return {
            "ok": True,
            "deleted_vectors": deleted_vectors,
        }

    def load_document(self):
        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]), tuple(chroma_conf["allow_knowledge_file_type"])
        )

        for path in allowed_files_path:
            try:
                self.ingest_file(path)
            except Exception as e:
                logger.error(f"[加载知识库] {path} 加载失败：{str(e)}", exc_info=True)
                continue


if __name__ == "__main__":
    store = VectorStoreService()
    store.load_document()
    res = store.search_with_filters("牛顿第二定律", k=3, subject="计算机网络", grade="大二", author="谢希仁")
    for doc, score in res:
        print(score, doc.page_content[:80])
        print(doc.metadata)
        print("-" * 20)
