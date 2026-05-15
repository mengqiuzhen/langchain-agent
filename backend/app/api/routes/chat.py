from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.app_state import get_agent
from backend.app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    service = ChatService(get_agent())
    try:
        answer = service.ask(query=request.query, subject=request.subject)
        return ChatResponse(answer=answer)
    except ValueError as exc:
        err_text = str(exc)
        if "InvalidApiKey" in err_text or "401" in err_text:
            raise HTTPException(status_code=401, detail="通义 API Key 无效或未生效") from exc
        raise HTTPException(status_code=400, detail=err_text) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    service = ChatService(get_agent())

    def event_generator():
        try:
            for chunk in service.ask_stream(query=request.query, subject=request.subject):
                if chunk.startswith("\n__CLEANED_FINAL__:"):
                    final_answer = chunk.removeprefix("\n__CLEANED_FINAL__:")
                    yield f"event: done\ndata: {json.dumps({'answer': final_answer}, ensure_ascii=False)}\n\n"
                else:
                    yield f"event: message\ndata: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        except ValueError as exc:
            err_text = str(exc)
            message = "通义 API Key 无效或未生效" if ("InvalidApiKey" in err_text or "401" in err_text) else err_text
            yield f"event: error\ndata: {json.dumps({'detail': message}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
