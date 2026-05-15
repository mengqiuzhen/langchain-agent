from __future__ import annotations

from typing import Generator

from agent.react_agent import ReactAgent


NO_ANSWER_TEXT = "抱歉，我暂时无法生成有效回答，请换个问法再试。"


class ChatService:
    def __init__(self, agent: ReactAgent):
        self.agent = agent

    @staticmethod
    def _clean_answer(answer: str) -> str:
        filtered_lines: list[str] = []
        seen_lines: set[str] = set()

        for line in answer.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("【课程】") or stripped.startswith("【问题】"):
                continue
            low = stripped.lower()
            if "tool" in low:
                continue
            if "我将基于此进行查询" in stripped:
                continue
            if "根据工具" in stripped or "调用工具" in stripped:
                continue
            if stripped in seen_lines:
                continue
            seen_lines.add(stripped)
            filtered_lines.append(stripped)

        cleaned = "\n".join(filtered_lines).strip()
        return cleaned or NO_ANSWER_TEXT

    @staticmethod
    def _build_full_query(subject: str, query: str) -> str:
        course = subject or "全部"
        return f"【课程】{course}\n【问题】{query.strip()}"

    def ask(self, query: str, subject: str = "全部") -> str:
        full_query = self._build_full_query(subject=subject, query=query)
        chunks = list(self.agent.execute_stream(full_query))
        answer = "".join(chunks).strip()
        return self._clean_answer(answer)

    def ask_stream(self, query: str, subject: str = "全部") -> Generator[str, None, None]:
        full_query = self._build_full_query(subject=subject, query=query)
        collected: list[str] = []
        for chunk in self.agent.execute_stream(full_query):
            collected.append(chunk)
            yield chunk

        cleaned = self._clean_answer("".join(collected).strip())
        yield f"\n__CLEANED_FINAL__:{cleaned}"
