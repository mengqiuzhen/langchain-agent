from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from backend.app.schemas.knowledge import (
    DeleteKnowledgeFileResponse,
    KnowledgeFileItem,
    KnowledgeFileListResponse,
    SubjectListResponse,
    UploadResult,
)
from backend.app.services.app_state import get_vector_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/subjects", response_model=SubjectListResponse)
def list_subjects() -> SubjectListResponse:
    vector_store = get_vector_store()
    try:
        records = vector_store.vector_store.get(include=["metadatas"])
        metadatas = records.get("metadatas", []) if records else []
        subjects = sorted({m.get("subject") for m in metadatas if m and m.get("subject")})
        return SubjectListResponse(subjects=["全部", *subjects] if subjects else ["全部"])
    except Exception:
        return SubjectListResponse(subjects=["全部"])


@router.get("/files", response_model=KnowledgeFileListResponse)
def list_knowledge_files() -> KnowledgeFileListResponse:
    vector_store = get_vector_store()
    files = vector_store.list_ingested_files()
    return KnowledgeFileListResponse(files=[KnowledgeFileItem(**item) for item in files])


@router.delete("/file", response_model=DeleteKnowledgeFileResponse)
def delete_knowledge_file(
    source: str = Query(default="", description="教材文件名（source）"),
    file_md5: str = Query(default="", description="教材文件 MD5"),
) -> DeleteKnowledgeFileResponse:
    if not source.strip() and not file_md5.strip():
        raise HTTPException(status_code=400, detail="source 或 file_md5 至少传一个")

    vector_store = get_vector_store()
    result = vector_store.delete_by_source_or_md5(source=source, file_md5=file_md5)
    return DeleteKnowledgeFileResponse(**result)


@router.post("/upload", response_model=UploadResult)
async def upload_knowledge(
    files: list[UploadFile] = File(...),
    subject: str = Form("计算机网络"),
    grade: str = Form("大一"),
    author: str = Form("未填写"),
) -> UploadResult:
    vector_store = get_vector_store()
    success_count = 0
    duplicate_count = 0
    empty_count = 0
    failed_count = 0
    chunk_count = 0
    failed_details: list[str] = []
    metadata = {
        "subject": subject.strip() or "未分类",
        "grade": grade,
        "author": author.strip() or "未分类",
    }

    for file in files:
        filename = file.filename or "unknown.pdf"

        if not filename.lower().endswith(".pdf"):
            failed_count += 1
            failed_details.append(f"{filename}: 文件类型不支持，仅支持 PDF")
            continue

        try:
            data = await file.read()
            if not data:
                failed_count += 1
                failed_details.append(f"{filename}: 文件为空")
                continue

            inserted, status = vector_store.ingest_uploaded_pdf_bytes_with_status(
                filename,
                data,
                metadata=metadata,
            )
            if status == "inserted":
                success_count += 1
                chunk_count += inserted
            elif status == "duplicate":
                duplicate_count += 1
            elif status == "empty_content":
                empty_count += 1
            else:
                failed_count += 1
                failed_details.append(f"{filename}: 入库失败，状态={status}")
        except ValueError as exc:
            err_text = str(exc)
            if "InvalidApiKey" in err_text or "401" in err_text:
                raise HTTPException(status_code=401, detail="通义 API Key 无效或未生效") from exc
            failed_count += 1
            failed_details.append(f"{filename}: {err_text}")
        except HTTPException:
            raise
        except Exception as exc:
            failed_count += 1
            failed_details.append(f"{filename}: {str(exc)}")

    return UploadResult(
        success_count=success_count,
        duplicate_count=duplicate_count,
        empty_count=empty_count,
        failed_count=failed_count,
        chunk_count=chunk_count,
        subject=metadata["subject"],
        grade=metadata["grade"],
        author=metadata["author"],
        failed_details=failed_details,
    )
