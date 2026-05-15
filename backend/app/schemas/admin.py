from pydantic import BaseModel, Field


class AdminResetResponse(BaseModel):
    ok: bool
    deleted_vectors: int


class AdminLogTailResponse(BaseModel):
    log_file: str
    lines: list[str] = Field(default_factory=list)


class AdminOverviewResponse(BaseModel):
    metrics_summary: dict
    knowledge_file_count: int
    knowledge_chunk_count: int
