import time

from langchain.agents import create_agent

from agent.tools.agent_tools import (
    analyze_student_scores,
    query_student_scores,
    query_uploaded_file,
    rag_summarize,
    search_tech_qa,
)
from agent.tools.middleware import log_before_model, monitor_tool
from model.factory import chat_model
from utils.metrics import track_event
from utils.prompt_loader import load_system_prompt


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[
                rag_summarize,
                query_student_scores,
                analyze_student_scores,
                search_tech_qa,
                query_uploaded_file,
            ],
            middleware=[monitor_tool, log_before_model],
        )

    def execute_stream(self, query):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        start = time.time()
        last_assistant_content = ""
        try:
            for chunk in self.agent.stream(input_dict, stream_mode="values", context={}):
                latest_message = chunk["messages"][-1]

                msg_type = getattr(latest_message, "type", "")
                if msg_type not in ("ai", "assistant"):
                    continue

                content = getattr(latest_message, "content", "") or ""
                if isinstance(content, list):
                    content = "".join(str(x) for x in content)
                else:
                    content = str(content)

                if not content.strip():
                    continue

                # 仅输出新增增量，避免流式阶段重复输出整段答案
                if content.startswith(last_assistant_content):
                    delta = content[len(last_assistant_content):]
                else:
                    delta = content

                if delta:
                    yield delta
                    last_assistant_content = content

            latency_ms = int((time.time() - start) * 1000)
            track_event({"type": "query", "status": "success", "latency_ms": latency_ms})
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            track_event({"type": "query", "status": "failed", "latency_ms": latency_ms, "error": str(e)})
            raise


if __name__ == "__main__":
    agent = ReactAgent()
    for chunk in agent.execute_stream("谁的计算机网络成绩最高"):
        print(chunk, end="", flush=True)
