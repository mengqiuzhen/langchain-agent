# AI教学助手（FastAPI + Next.js）

基于 `FastAPI + Next.js + LangChain` 的 AI 教学助手，面向教学资料入库、学生问答、管理员运维管理等场景。

当前系统已支持：
- 管理员 / 教师 / 学生 三类账号与权限控制
- 教师端教材 PDF 入库与删除
- 学生端教学问答
- 管理员端日志查看、数据库重置、账号创建、密码重置
- 用户数据使用 `SQLAlchemy + SQLite`
- 向量数据库支持 `Chroma` 与 `Milvus` 切换

---

## 1. 当前技术栈

### 后端
- `FastAPI`
- `Uvicorn`
- `SQLAlchemy`
- `LangChain`
- `Chroma / Milvus`
- `DashScope`
- `PyMuPDF + RapidOCR`（用于扫描版/图片版 PDF OCR）

### 前端
- `Next.js`
- `React`
- `TypeScript`

---

## 2. 核心能力

### 2.1 管理员端
- 创建教师/学生账号
- 重置用户密码
- 查看系统日志
- 重置知识库数据
- 查看系统运行概览

### 2.2 教师端
- 上传多个教材 PDF 入库
- 维护教材元信息（学科、年级、作者）
- 删除单个教材
- 查看运行指标
- 同时可访问学生端功能

### 2.3 学生端
- 选择课程并发起问答
- 通过 Agent + RAG 基于教材内容获取回答

---

## 3. 项目结构

```text
a/
├─ backend/
│  ├─ app/
│  │  ├─ api/routes/
│  │  ├─ core/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ db.py
│  │  ├─ models.py
│  │  └─ main.py
│  └─ requirements.txt
├─ frontend/
│  ├─ app/
│  ├─ lib/
│  ├─ package.json
│  └─ tsconfig.json
├─ rag/
├─ agent/
├─ model/
├─ utils/
├─ config/
├─ data/
└─ README.md
```

---

## 4. 环境变量

### 必填

```powershell
$env:DASHSCOPE_API_KEY="你的apikey"
```

### 可选

```powershell
$env:BING_SEARCH_API_KEY="你的key"
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
$env:BOOTSTRAP_ADMIN_EMAIL="admin@example.com"
$env:BOOTSTRAP_ADMIN_PASSWORD="admin123456"
$env:AUTH_SECRET="dev-auth-secret-change-me"
$env:DATABASE_URL="sqlite:///E:/Code/projects/AI/a/data/app.db"
$env:VECTOR_BACKEND="chroma"
$env:MILVUS_URI="http://127.0.0.1:19530"
$env:MILVUS_COLLECTION="agent"
```

说明：
- `VECTOR_BACKEND` 默认是 `chroma`
- 设置为 `milvus` 后，后端将切换到 Milvus 向量库
- `DATABASE_URL` 不设置时默认使用 `a/data/app.db`

---

## 5. 推荐启动方式：使用虚拟环境

以下示例基于 Windows PowerShell。

### 5.1 创建并激活虚拟环境

在项目根目录 `a/` 下执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

激活成功后，终端前面通常会出现 `(.venv)`。

### 5.2 安装后端依赖

```powershell
pip install -r backend/requirements.txt
```

### 5.3 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

---

## 6. 启动方式

### 6.1 启动后端

确保当前目录在项目根目录 `a/`，且虚拟环境已激活：

```powershell
uvicorn backend.app.main:app --reload
```

默认地址：`http://127.0.0.1:8000`

常用测试地址：
- 健康检查：`http://127.0.0.1:8000/health`
- Swagger 文档：`http://127.0.0.1:8000/docs`

### 6.2 启动前端

另开一个终端，进入项目根目录并激活虚拟环境后执行：

```powershell
cd frontend
npm run dev
```

前端默认地址：`http://localhost:3000`

---

## 7. 默认测试账号

系统启动时会自动创建以下测试账号（若数据库中不存在）：

### 管理员
- `admin@example.com` / `admin123456`

### 教师
- `teacher1@example.com` / `teacher123`
- `teacher2@example.com` / `teacher123`

### 学生
- `student1@example.com` / `student123`
- `student2@example.com` / `student123`
- `student3@example.com` / `student123`

---

## 8. 权限说明

### 管理员
可访问：
- 管理员端
- 教师端
- 学生端
- 运行指标

### 教师
可访问：
- 教师端
- 学生端
- 运行指标

### 学生
可访问：
- 学生端

说明：
- 未登录状态下不会显示受保护功能入口
- 登录后导航栏会显示当前登录用户与角色
- 登录按钮会自动变为退出登录

---

## 9. API 概览

### 认证与用户管理
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/auth/users`（管理员）
- `POST /api/auth/users`（管理员创建账号）
- `POST /api/auth/users/reset-password`（管理员重置密码）

### 教材知识库
- `GET /api/knowledge/subjects`
- `GET /api/knowledge/files`
- `POST /api/knowledge/upload`
- `DELETE /api/knowledge/file`

### 问答
- `POST /api/chat`
- `POST /api/chat/stream`

### 运维与指标
- `GET /api/metrics/summary`（管理员 / 教师）
- `GET /api/admin/overview`（管理员）
- `GET /api/admin/logs/tail`（管理员）
- `POST /api/admin/reset-db`（管理员）

---

## 10. 如何测试 SQLAlchemy 与 Milvus

### 测试 SQLAlchemy
1. 启动后端
2. 确认生成 `a/data/app.db`
3. 用默认测试账号登录
4. 管理员创建新账号
5. 管理员重置用户密码

### 测试 Milvus
1. 启动 Milvus 服务
2. 设置：

```powershell
$env:VECTOR_BACKEND="milvus"
$env:MILVUS_URI="http://127.0.0.1:19530"
$env:MILVUS_COLLECTION="agent"
```

3. 重启后端
4. 教师上传教材 PDF
5. 学生提问验证检索
6. 管理员执行数据库重置验证清空效果

---

## 11. 说明

- 当前 `app.py` 仍保留，仅作旧版 Streamlit 迁移参考
- 当前实际运行入口为：`FastAPI + Next.js`
- 用户系统已迁移到 `SQLAlchemy`
- 向量库已支持 `Chroma / Milvus` 双后端切换
