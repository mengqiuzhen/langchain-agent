from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query

from backend.app.core.auth_security import require_roles
from backend.app.schemas.admin import AdminLogTailResponse, AdminOverviewResponse, AdminResetResponse
from backend.app.services.app_state import get_vector_store
from utils.metrics import summarize_metrics
from utils.path_tools import get_abs_path

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])


def _tail_lines(path: Path, lines: int) -> list[str]:
    if not path.exists() or not path.is_file():
        return []

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        all_lines = f.readlines()
    return [line.rstrip("\n") for line in all_lines[-lines:]]


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview() -> AdminOverviewResponse:
    vector_store = get_vector_store()
    files = vector_store.list_ingested_files()
    knowledge_file_count = len(files)
    knowledge_chunk_count = sum(int(item.get("chunk_count", 0)) for item in files)

    return AdminOverviewResponse(
        metrics_summary=summarize_metrics(limit=500),
        knowledge_file_count=knowledge_file_count,
        knowledge_chunk_count=knowledge_chunk_count,
    )


@router.post("/reset-db", response_model=AdminResetResponse)
def reset_database() -> AdminResetResponse:
    vector_store = get_vector_store()
    result = vector_store.reset_store()
    return AdminResetResponse(**result)


@router.get("/logs/tail", response_model=AdminLogTailResponse)
def get_log_tail(
    file: str = Query(default="agent", description="日志文件名（不含路径）"),
    lines: int = Query(default=100, ge=1, le=1000),
) -> AdminLogTailResponse:
    safe_name = Path(file).name
    if not safe_name.endswith(".log"):
        safe_name = f"{safe_name}.log"

    log_path = Path(get_abs_path("logs")) / safe_name
    return AdminLogTailResponse(log_file=safe_name, lines=_tail_lines(log_path, lines))
