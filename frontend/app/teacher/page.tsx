"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE_URL, deleteKnowledgeFile, getKnowledgeFiles, KnowledgeFileItem } from "@/lib/api";
import { validateSession } from "@/lib/auth";

const gradeOptions = ["大一", "大二", "大三", "大四", "研一", "研二", "其他"];

type UploadResult = {
  success_count: number;
  duplicate_count: number;
  empty_count: number;
  failed_count: number;
  chunk_count: number;
  subject: string;
  grade: string;
  author: string;
  failed_details?: string[];
};

export default function TeacherPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [subject, setSubject] = useState("计算机网络");
  const [grade, setGrade] = useState("大一");
  const [author, setAuthor] = useState("未填写");
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");

  const [knowledgeFiles, setKnowledgeFiles] = useState<KnowledgeFileItem[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [deleteLoadingMd5, setDeleteLoadingMd5] = useState<string>("");

  async function refreshKnowledgeFiles() {
    setListLoading(true);
    try {
      const items = await getKnowledgeFiles();
      setKnowledgeFiles(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取教材列表失败");
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    validateSession().then((me) => {
      if (!me || (me.role !== "teacher" && me.role !== "admin")) {
        window.location.href = "/login";
      }
    });
    refreshKnowledgeFiles();
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!files || files.length === 0) {
      setError("请先选择 PDF 文件");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("subject", subject);
      formData.append("grade", grade);
      formData.append("author", author);
      Array.from(files).forEach((file) => formData.append("files", file));

      const response = await fetch(`${API_BASE_URL}/api/knowledge/upload`, {
        method: "POST",
        body: formData,
      });

      const data = (await response.json()) as UploadResult | { detail?: string };
      if (!response.ok) {
        throw new Error("detail" in data ? data.detail ?? "上传失败" : "上传失败");
      }

      setResult(data as UploadResult);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setFiles(null);
      await refreshKnowledgeFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(item: KnowledgeFileItem) {
    if (!item.file_md5) {
      setError(`教材 ${item.source} 缺少 file_md5，无法安全删除`);
      return;
    }

    if (!window.confirm(`确认删除教材《${item.source}》？该操作不可撤销。`)) return;

    setDeleteLoadingMd5(item.file_md5);
    setError("");
    try {
      const res = await deleteKnowledgeFile(item.file_md5);
      if (!res.deleted) {
        throw new Error("未删除任何数据，请刷新后重试");
      }
      await refreshKnowledgeFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeleteLoadingMd5("");
    }
  }

  const selectedCount = files ? files.length : 0;

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1>教师端：教材管理</h1>
        <p>上传教材 PDF 入库，管理已入库的教材文件</p>
      </div>

      <div className="panel-layout">
        <div className="panel-side">
          <div className="card">
            <div className="card-header">
              <h2>上传教材</h2>
              <p>支持一次上传多个 PDF 文件</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">学科</label>
                <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="如：计算机网络" />
              </div>
              <div className="form-group">
                <label className="form-label">年级</label>
                <select value={grade} onChange={(e) => setGrade(e.target.value)}>
                  {gradeOptions.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">教材作者</label>
                <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="如：谢希仁" />
              </div>
              <div className="form-group">
                <label className="form-label">
                  选择 PDF 文件{selectedCount > 0 ? `（已选 ${selectedCount} 个）` : ""}
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={(e) => setFiles(e.target.files)}
                />
              </div>
              <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                {loading ? "正在入库..." : "开始入库"}
              </button>
            </form>

            {error ? <div className="alert alert-error">{error}</div> : null}

            {result ? (
              <div className="upload-result">
                <h3>入库结果</h3>
                <p>新增 {result.success_count} 个文件，共 {result.chunk_count} 个分片</p>
                <p>学科：{result.subject} / 年级：{result.grade} / 作者：{result.author}</p>
                <p>重复：{result.duplicate_count} / 空内容：{result.empty_count} / 失败：{result.failed_count}</p>
                {result.failed_details && result.failed_details.length > 0 ? (
                  <ul className="tool-list" style={{ marginTop: 8 }}>
                    {result.failed_details.map((line, i) => (
                      <li key={i}>{line}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>

        <div>
          <div className="card">
            <div className="card-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <h2>已入库教材</h2>
                <p>删除时会保留被其他教材引用的共享内容</p>
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={refreshKnowledgeFiles}
                disabled={listLoading}
              >
                {listLoading ? "刷新中..." : "刷新列表"}
              </button>
            </div>

            {knowledgeFiles.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "center", padding: "32px 0" }}>
                暂无教材记录
              </p>
            ) : (
              <div className="file-list">
                {knowledgeFiles.map((item) => (
                  <div key={item.file_md5 || item.source} className="file-item">
                    <div className="file-item-info">
                      <div className="file-item-name">{item.source}</div>
                      <div className="file-item-meta">分片数：{item.chunk_count}</div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-danger btn-sm"
                      disabled={deleteLoadingMd5 === item.file_md5}
                      onClick={() => handleDelete(item)}
                    >
                      {deleteLoadingMd5 === item.file_md5 ? "删除中..." : "删除"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
