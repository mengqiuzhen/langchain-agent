"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { API_BASE_URL, getSubjects } from "@/lib/api";
import { validateSession } from "@/lib/auth";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type StreamEvent = {
  event: string;
  data: string;
};

function parseSseChunk(buffer: string): { events: StreamEvent[]; remain: string } {
  const blocks = buffer.split("\n\n");
  const completeBlocks = blocks.slice(0, -1);
  const remain = blocks[blocks.length - 1] ?? "";

  const events: StreamEvent[] = [];
  for (const block of completeBlocks) {
    const lines = block.split("\n");
    let event = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    events.push({ event, data: dataLines.join("\n") });
  }

  return { events, remain };
}

const ANSWER_MODES = [
  { key: "知识讲解", label: "📖 知识讲解", desc: "概念解释与原理拆解" },
  { key: "例题讲解", label: "✏️ 例题讲解", desc: "生成例题与分步解题" },
  { key: "课堂出题", label: "📝 课堂出题", desc: "生成课堂练习题" },
  { key: "错因分析", label: "🔍 错因分析", desc: "常见错误与纠正方法" },
];

export default function StudentPage() {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [subjects, setSubjects] = useState<string[]>(["全部"]);
  const [subject, setSubject] = useState("全部");
  const [mode, setMode] = useState("知识讲解");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "你好，我是你的 AI 教学助手。你可以问我教材里的知识点、例题与解题思路。",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    validateSession().then((me) => {
      if (!me || (me.role !== "student" && me.role !== "teacher" && me.role !== "admin")) {
        window.location.href = "/login";
      }
    });

    getSubjects()
      .then((items) => {
        setSubjects(items);
        setSubject(items[0] ?? "全部");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "获取课程失败");
      });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = query.trim();
    if (!question) return;

    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
    setLoading(true);
    setError("");
    setQuery("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, subject, mode }),
      });

      if (!response.ok || !response.body) {
        throw new Error("问答失败");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const { events, remain } = parseSseChunk(buffer);
        buffer = remain;

        for (const evt of events) {
          if (evt.event === "message") {
            try {
              const payload = JSON.parse(evt.data) as { chunk?: string };
              const chunk = payload.chunk ?? "";
              if (!chunk) continue;

              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (!last || last.role !== "assistant") return prev;
                next[next.length - 1] = { ...last, content: last.content + chunk };
                return next;
              });
            } catch {
              // ignore malformed stream chunk
            }
          } else if (evt.event === "done") {
            try {
              const payload = JSON.parse(evt.data) as { answer?: string };
              const finalAnswer = payload.answer ?? "";
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (!last || last.role !== "assistant") return prev;
                next[next.length - 1] = { ...last, content: finalAnswer || last.content };
                return next;
              });
            } catch {
              // ignore malformed done payload
            }
          } else if (evt.event === "error") {
            try {
              const payload = JSON.parse(evt.data) as { detail?: string };
              throw new Error(payload.detail ?? "问答失败");
            } catch {
              throw new Error("问答失败");
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "问答失败");
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const next = [...prev];
        const last = next[next.length - 1];
        if (last.role === "assistant" && !last.content.trim()) {
          next.pop();
        }
        return next;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1>学生端：教学问答</h1>
        <p>选择课程与回答模式，基于教材内容获取 AI 精准回答</p>
      </div>

      <div className="panel-layout">
        <div className="panel-side">
          <div className="card">
            <div className="card-header">
              <h2>课程设置</h2>
            </div>
            <div className="form-group">
              <label className="form-label">学科</label>
              <select value={subject} onChange={(e) => setSubject(e.target.value)}>
                {subjects.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2>回答模式</h2>
            </div>
            <div className="mode-list">
              {ANSWER_MODES.map((m) => (
                <button
                  key={m.key}
                  type="button"
                  className={`mode-option ${mode === m.key ? "active" : ""}`}
                  onClick={() => setMode(m.key)}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="chat-container">
            <div className="chat-messages">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`chat-bubble ${message.role}`}>
                  {message.content || (
                    <span>
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </span>
                  )}
                </div>
              ))}
              {error ? (
                <div className="alert alert-error" style={{ margin: "0 16px" }}>{error}</div>
              ) : null}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="chat-input-row">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入你的问题，例如：请解释 TCP 三次握手..."
                disabled={loading}
              />
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? "生成中..." : "发送"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
