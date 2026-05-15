"use client";

import { FormEvent, useEffect, useState } from "react";
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

export default function StudentPage() {
  const [subjects, setSubjects] = useState<string[]>(["全部"]);
  const [subject, setSubject] = useState("全部");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "你好，我是你的AI教学助手。你可以问我教材里的知识点、例题与解题思路。",
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = query.trim();
    if (!question) {
      return;
    }

    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
    setLoading(true);
    setError("");
    setQuery("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, subject }),
      });

      if (!response.ok || !response.body) {
        throw new Error("问答失败");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

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
    <div className="grid" style={{ alignItems: "start" }}>
      <div className="card">
        <h1>学生端：教学问答</h1>
        <label>
          课程（学科）
          <select value={subject} onChange={(e) => setSubject(e.target.value)}>
            {subjects.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <form onSubmit={handleSubmit}>
          <label>
            输入问题
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：请解释TCP三次握手并给一道例题"
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "教学助手生成中..." : "发送问题"}
          </button>
        </form>
        {error ? <p className="status">错误：{error}</p> : null}
      </div>

      <div className="card">
        <h2>对话记录</h2>
        <div className="chat-box">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
              {message.content}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
