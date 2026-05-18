"use client";

import { useEffect, useState } from "react";
import { getMetricsSummary, type MetricsSummary } from "@/lib/api";
import { getToken, validateSession } from "@/lib/auth";

export default function MetricsPage() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    validateSession().then(async (me) => {
      if (!me || me.role !== "admin") {
        window.location.href = "/login";
        return;
      }

      try {
        const token = getToken();
        const res = await getMetricsSummary(token);
        setSummary(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取运行指标失败");
      }
    });
  }, []);

  return (
    <div className="animate-in">
      <div className="page-header">
        <h1>运行指标</h1>
        <p>系统问答统计、成功率与工具调用分析</p>
      </div>

      {error ? <div className="alert alert-error">{error}</div> : null}

      {summary ? (
        <>
          <div className="metrics-grid">
            <div className="metric">
              <div className="metric-label">总问答数</div>
              <div className="metric-value">{summary.total_queries}</div>
            </div>
            <div className="metric">
              <div className="metric-label">成功数</div>
              <div className="metric-value">{summary.success_queries}</div>
            </div>
            <div className="metric">
              <div className="metric-label">成功率</div>
              <div className="metric-value">{summary.success_rate.toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div className="metric-label">平均耗时</div>
              <div className="metric-value">{summary.avg_latency_ms.toFixed(0)} ms</div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2>工具调用统计</h2>
              <p>近 500 条事件的工具调用次数分布</p>
            </div>
            {Object.keys(summary.tool_counts).length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 14, textAlign: "center", padding: "24px 0" }}>
                暂无工具调用事件
              </p>
            ) : (
              <ul className="tool-list">
                {Object.entries(summary.tool_counts).map(([tool, count]) => (
                  <li key={tool}>
                    {tool}：{count}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      ) : (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "48px 0" }}>
          加载中...
        </p>
      )}
    </div>
  );
}
