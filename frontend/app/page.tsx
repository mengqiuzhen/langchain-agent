import Link from "next/link";

export default function HomePage() {
  return (
    <div className="animate-in">
      <section className="hero">
        <h1>AI 教学助手</h1>
        <p>基于 LangChain + RAG 的智能教学知识库问答系统</p>
      </section>

      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-label">支持角色</div>
          <div className="metric-value">3</div>
        </div>
        <div className="metric">
          <div className="metric-label">核心能力</div>
          <div className="metric-value">4</div>
        </div>
        <div className="metric">
          <div className="metric-label">向量引擎</div>
          <div className="stat-value" style={{ fontSize: 24 }}>Chroma / Milvus</div>
        </div>
      </div>

      <div className="section-title" style={{ marginBottom: 16 }}>快速入口</div>
      <div className="quick-links">
        <Link href="/teacher" className="quick-link-card">
          <div className="quick-link-icon" style={{ background: "rgba(59,130,246,0.12)" }}>📚</div>
          <h3>教师端</h3>
          <p>上传教材 PDF，填写学科、年级、作者后写入向量知识库，管理已入库教材。</p>
        </Link>
        <Link href="/student" className="quick-link-card">
          <div className="quick-link-icon" style={{ background: "rgba(139,92,246,0.12)" }}>🎓</div>
          <h3>学生端</h3>
          <p>选择课程后发起教学问答，基于教材内容获取 AI 精准回答。</p>
        </Link>
        <Link href="/admin" className="quick-link-card">
          <div className="quick-link-icon" style={{ background: "rgba(34,197,94,0.1)" }}>⚙️</div>
          <h3>管理员端</h3>
          <p>系统概览、账号分配、密码重置、日志监控与数据库管理。</p>
        </Link>
        <Link href="/metrics" className="quick-link-card">
          <div className="quick-link-icon" style={{ background: "rgba(251,191,36,0.1)" }}>📊</div>
          <h3>运行指标</h3>
          <p>问答统计、成功率、平均耗时与工具调用分析。</p>
        </Link>
      </div>
    </div>
  );
}
