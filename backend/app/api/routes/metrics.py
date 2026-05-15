from fastapi import APIRouter, Depends

from backend.app.core.auth_security import require_roles
from backend.app.schemas.metrics import MetricsSummaryResponse
from utils.metrics import summarize_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
def metrics_summary(_: dict = Depends(require_roles("admin", "teacher"))) -> MetricsSummaryResponse:
    summary = summarize_metrics(limit=500)
    return MetricsSummaryResponse(**summary)
