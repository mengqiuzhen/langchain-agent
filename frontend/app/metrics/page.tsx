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
    <div className="card">
      <h1>运行指标</h1>
      <p>展示近 500 条事件的汇总结果。</p>

      {error ? <p className="status">错误：{error}</p> : null}

      {summary ? (
        <>
          <div className="metrics-grid">
            <div className="metric">
              <div>总问答数</div>
              <div className="metric-value">{summary.total_queries}</div>
            </div>
            <div className="metric">
              <div>成功问答数</div>
              <div className="metric-value">{summary.success_queries}</div>
            </div>
            <div className="metric">
              <div>问答成功率</div>
              <div className="metric-value">{summary.success_rate.toFixed(1)}%</div>
            </div>
            <div className="metric">
              <div>平均耗时</div>
              <div className="metric-value">{summary.avg_latency_ms.toFixed(0)} ms</div>
            </div>
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <h3>工具调用次数</h3>
            {Object.keys(summary.tool_counts).length === 0 ? (
              <p>暂无工具调用事件</p>
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
      ) : null}
    </div>
  );
}
