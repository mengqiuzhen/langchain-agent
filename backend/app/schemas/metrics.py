from pydantic import BaseModel, Field


class MetricsSummaryResponse(BaseModel):
    total_queries: int
    success_queries: int
    success_rate: float
    avg_latency_ms: float
    tool_counts: dict[str, int] = Field(default_factory=dict)
