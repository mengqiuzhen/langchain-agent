export default function HomePage() {
  return (
    <div>
      <section className="hero card">
        <h1>AI教学助手</h1>
        <p>已将原 Streamlit 结构迁移为 FastAPI + Next.js 的前后端分离架构。</p>
        <p>当前保留核心能力：教材入库、教学问答。</p>
      </section>

      <section className="grid">
        <div className="card">
          <h2>教师端</h2>
          <p>上传教材 PDF，填写学科、年级、作者后写入向量知识库。</p>
        </div>
        <div className="card">
          <h2>学生端</h2>
          <p>选择课程后发起教学问答，后端继续复用现有 Agent 与 RAG 逻辑。</p>
        </div>
      </section>
    </div>
  );
}
