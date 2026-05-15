import math
import re
from collections import defaultdict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from model.factory import chat_model
from rag.vector_store import VectorStoreService
from utils.config_handler import chroma_conf, prompts_conf
from utils.logger_handler import logger
from utils.path_tools import get_abs_path


class RagSummarizeService:
    _PROMPT_TEXT: str = None

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.prompt_text = self._load_prompt_text()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _load_prompt_text(self) -> str:
        if self._PROMPT_TEXT is not None:
            return self._PROMPT_TEXT

        path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])
        try:
            with open(path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()
        except PermissionError:
            logger.error(f"无权限读取提示词文件：{path}")
            raise PermissionError(f"无权限读取提示词文件：{path}")
        except UnicodeDecodeError:
            logger.error(f"提示词文件编码错误（需UTF-8）：{path}")
            raise ValueError(f"提示词文件编码错误（需UTF-8）：{path}")
        except Exception as e:
            logger.error(f"读取提示词文件失败：{str(e)}")
            raise RuntimeError(f"读取提示词文件失败：{str(e)}")

        if not prompt_text:
            logger.error(f"提示词文件内容为空：{path}")
            raise ValueError(f"提示词文件内容为空：{path}")

        self._PROMPT_TEXT = prompt_text
        return prompt_text

    def _init_chain(self):
        return self.prompt_template | self.model | StrOutputParser()

    @staticmethod
    def _tokenize_for_overlap(text: str) -> set[str]:
        text = (text or "").lower()
        cn_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        en_chunks = re.findall(r"[a-z0-9_]{2,}", text)
        return set(cn_chunks + en_chunks)

    @staticmethod
    def _expand_exam_query(query: str) -> list[str]:
        expanded = [query]
        match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*题", query)
        if not match:
            return expanded

        raw = match.group(1)
        cn2num = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        }

        if raw.isdigit():
            num = int(raw)
        else:
            num = cn2num.get(raw)

        if not num:
            return expanded

        variants = [
            f"第{num}题",
            f"{num}题",
            f"{num}.",
            f"第{raw}题",
        ]

        for v in variants:
            if v not in expanded:
                expanded.append(v)

        return expanded

    @staticmethod
    def _rewrite_query(query: str) -> list[str]:
        """轻量 query rewrite：避免引入额外模型调用成本。"""
        q = (query or "").strip()
        if not q:
            return []

        variants = [q]

        # 去掉常见口语前后缀
        normalized = re.sub(r"^(请问|帮我|麻烦|请你|请)", "", q)
        normalized = re.sub(r"(谢谢|可以吗|好吗|呀|吧)$", "", normalized).strip(" ，。！？?!.")
        if normalized and normalized not in variants:
            variants.append(normalized)

        # 关键词版（用于提高召回）
        keyword_text = re.sub(r"[^\u4e00-\u9fffa-zA-Z0-9]+", " ", normalized or q)
        stop_words = {
            "请", "请问", "帮我", "解释", "说明", "分析", "一下", "这个", "那个", "如何", "为什么", "什么", "怎么",
            "the", "and", "for", "with", "from", "that", "this",
        }
        tokens = [t for t in keyword_text.split() if len(t) >= 2 and t.lower() not in stop_words]
        if tokens:
            keyword_query = " ".join(tokens[:8])
            if keyword_query and keyword_query not in variants:
                variants.append(keyword_query)

        return variants

    @staticmethod
    def _rerank(query: str, candidates: list[tuple]) -> list[tuple]:
        """
        简单重排：融合向量分数 + 关键词重合度。
        向量分数越低越好；关键词重合越高越好。
        """
        if not candidates:
            return []

        query_tokens = RagSummarizeService._tokenize_for_overlap(query)
        if not query_tokens:
            return candidates

        vector_scores = [float(score) for _, score in candidates]
        min_s, max_s = min(vector_scores), max(vector_scores)
        denom = max(max_s - min_s, 1e-9)

        reranked = []
        for doc, score in candidates:
            doc_text = doc.page_content or ""
            doc_tokens = RagSummarizeService._tokenize_for_overlap(doc_text)
            overlap = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)

            # 向量分归一到[0,1]后取反（高分更好）
            vector_good = 1.0 - ((float(score) - min_s) / denom)
            final = 0.7 * vector_good + 0.3 * overlap
            reranked.append((doc, score, final))

        reranked.sort(key=lambda x: x[2], reverse=True)
        return [(doc, score) for doc, score, _ in reranked]

    def retrieve_docs_with_scores(
        self,
        query: str,
        k: int | None = None,
        subject: str = "全部",
        grade: str = "全部",
        author: str = "全部",
    ):
        top_k = k if k is not None else chroma_conf.get("k", 3)

        # 多路召回：原始query + rewrite变体 + 题号扩展
        routes = []
        for q in self._rewrite_query(query):
            routes.extend(self._expand_exam_query(q))

        if not routes:
            routes = [query]

        route_counter = defaultdict(int)
        merged = []
        seen = set()

        per_route_k = max(top_k, 6)
        for q in routes:
            route_counter[q] += 1
            docs = self.vector_store.search_with_filters(
                query=q,
                k=per_route_k,
                subject=subject,
                grade=grade,
                author=author,
            )
            for doc, score in docs:
                key = (
                    (doc.page_content or "")[:160],
                    doc.metadata.get("source", ""),
                    doc.metadata.get("page", doc.metadata.get("page_number", "")),
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append((doc, score))

        reranked = self._rerank(query=query, candidates=merged)
        return reranked[:top_k]

    @staticmethod
    def _build_mode_instruction(mode: str) -> str:
        mode_map = {
            "知识讲解": "请优先给出概念解释与原理拆解，并结合教材语境说明。",
            "例题讲解": "请围绕该问题生成1道贴近教材的例题，并提供分步解题过程。",
            "课堂出题": "请基于检索内容给出2道课堂练习题（含答案要点），难度中等。",
            "错因分析": "请先列出常见错误，再给出纠正方法与自检步骤。",
        }
        return mode_map.get(mode, "请给出清晰、结构化、简洁的教材化回答。")

    def _build_context_and_sources(
        self,
        query: str,
        k: int | None = None,
        subject: str = "全部",
        grade: str = "全部",
        author: str = "全部",
    ):
        docs_with_scores = self.retrieve_docs_with_scores(
            query=query,
            k=k,
            subject=subject,
            grade=grade,
            author=author,
        )
        context_parts = []
        sources = []

        for idx, (doc, score) in enumerate(docs_with_scores, start=1):
            metadata = doc.metadata or {}
            source = metadata.get("source", "未知来源")
            page = metadata.get("page", metadata.get("page_number", "-"))
            subject_meta = metadata.get("subject", "未分类")
            grade_meta = metadata.get("grade", "未分类")
            author_meta = metadata.get("author", "未分类")
            chunk_preview = doc.page_content.strip().replace("\n", " ")[:120]

            context_parts.append(
                f"【参考资料{idx}】来源:{source} 页码:{page} 学科:{subject_meta} 年级:{grade_meta} 作者:{author_meta} 相似度分数:{score}\n内容:{doc.page_content}"
            )
            sources.append(
                {
                    "index": idx,
                    "source": source,
                    "page": page,
                    "score": float(score),
                    "preview": chunk_preview,
                    "subject": subject_meta,
                    "grade": grade_meta,
                    "author": author_meta,
                }
            )

        return "\n".join(context_parts), sources

    def rag_summarize(self, query: str) -> str:
        context, _ = self._build_context_and_sources(query)
        input_dict = {"input": query, "context": context}
        return self.chain.invoke(input_dict)

    def answer_with_citations(
        self,
        query: str,
        mode: str = "知识讲解",
        subject: str = "全部",
        grade: str = "全部",
        author: str = "全部",
    ) -> dict:
        context, sources = self._build_context_and_sources(
            query,
            k=chroma_conf.get("k", 3),
            subject=subject,
            grade=grade,
            author=author,
        )

        prompt_input = {
            "input": f"{query}\n\n【回答模式要求】{self._build_mode_instruction(mode)}",
            "context": context,
        }
        answer = self.chain.invoke(prompt_input)
        return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    vs = VectorStoreService()
    rag = RagSummarizeService(vs)
    res = rag.answer_with_citations("请解释TCP三次握手", mode="知识讲解", subject="计算机网络", grade="大二", author="谢希仁")
    print(res["answer"])
    print(res["sources"])
