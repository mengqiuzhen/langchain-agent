"use client";

import { useEffect, useState } from "react";
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

    const ok = window.confirm(`确认删除教材《${item.source}》？该操作不可撤销。`);
    if (!ok) {
      return;
    }

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

  return (
    <div className="grid" style={{ alignItems: "start" }}>
      <div className="card">
        <h1>教师端：教材入库</h1>
        <p>支持一次上传多个 PDF 文件，保留原有入库逻辑与去重逻辑。</p>

        <form onSubmit={handleSubmit}>
          <div className="grid">
            <label>
              学科
              <input value={subject} onChange={(e) => setSubject(e.target.value)} />
            </label>

            <label>
              年级
              <select value={grade} onChange={(e) => setGrade(e.target.value)}>
                {gradeOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label>
              教材作者
              <input value={author} onChange={(e) => setAuthor(e.target.value)} />
            </label>
          </div>

          <label>
            选择教材 PDF
            <input type="file" accept="application/pdf" multiple onChange={(e) => setFiles(e.target.files)} />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "正在入库..." : "开始入库"}
          </button>
        </form>

        {error ? <p className="status">错误：{error}</p> : null}

        {result ? (
          <div className="card" style={{ marginTop: 20 }}>
            <h3>入库结果</h3>
            <p>
              新增 {result.success_count} 个文件，共新增 {result.chunk_count} 个唯一文本分片。
            </p>
            <p>
              学科：{result.subject} / 年级：{result.grade} / 作者：{result.author}
            </p>
            <p>重复文件：{result.duplicate_count}</p>
            <p>空内容文件：{result.empty_count}</p>
            <p>处理失败文件：{result.failed_count}</p>
            {result.failed_details && result.failed_details.length > 0 ? (
              <div>
                <p>失败详情：</p>
                <ul className="tool-list">
                  {result.failed_details.map((line, index) => (
                    <li key={`${line}-${index}`}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="card">
        <h2>教材管理（单个删除）</h2>
        <p>删除时会保留仍被其他教材引用的共享内容，只移除真正无引用的分片。</p>

        <button type="button" onClick={refreshKnowledgeFiles} disabled={listLoading}>
          {listLoading ? "刷新中..." : "刷新教材列表"}
        </button>

        <div style={{ marginTop: 12 }}>
          {knowledgeFiles.length === 0 ? (
            <p>暂无教材记录</p>
          ) : (
            <ul className="tool-list">
              {knowledgeFiles.map((item) => (
                <li key={item.file_md5 || item.source} style={{ marginBottom: 12 }}>
                  <div>
                    <strong>{item.source}</strong>
                  </div>
                  <div>分片数：{item.chunk_count}</div>
                  <button
                    type="button"
                    style={{ marginTop: 8 }}
                    disabled={deleteLoadingMd5 === item.file_md5}
                    onClick={() => handleDelete(item)}
                  >
                    {deleteLoadingMd5 === item.file_md5 ? "删除中..." : "删除该教材"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
