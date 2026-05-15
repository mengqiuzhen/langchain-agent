from pydantic import BaseModel, Field


class UploadResult(BaseModel):
    success_count: int
    duplicate_count: int
    empty_count: int
    failed_count: int
    chunk_count: int
    subject: str
    grade: str
    author: str
    failed_details: list[str] = Field(default_factory=list)


class SubjectListResponse(BaseModel):
    subjects: list[str] = Field(default_factory=list)


class KnowledgeFileItem(BaseModel):
    source: str
    chunk_count: int
    file_md5: str = ""


class KnowledgeFileListResponse(BaseModel):
    files: list[KnowledgeFileItem] = Field(default_factory=list)


class DeleteKnowledgeFileResponse(BaseModel):
    deleted: bool
    deleted_chunks: int
    removed_md5: bool
