from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="学生提问内容")
    subject: str = Field(default="全部", description="课程/学科过滤")


class ChatResponse(BaseModel):
    answer: str
