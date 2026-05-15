from typing import Any, Callable

from langchain.agents import AgentState
from langchain.agents.middleware import before_model, wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command

from utils.logger_handler import logger
from utils.metrics import track_event


@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    logger.info(f"[tool monitor]执行工具: {request.tool_call['name']}")
    logger.info(f"[tool monitor]参数: {request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")
        track_event({"type": "tool", "status": "success", "tool": request.tool_call["name"]})
        return result
    except Exception as e:
        logger.info(f"工具{request.tool_call['name']}调用失败: {e}")
        track_event({"type": "tool", "status": "failed", "tool": request.tool_call["name"], "error": str(e)})
        raise


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    logger.info(f"[log_before_model]: 即将调用模型，带有{len(state['messages'])}条消息")
    logger.info(f"[log_before_model][{type(state['messages'][-1]).__name__}]: {state['messages'][-1].content.strip()}")
    return None
