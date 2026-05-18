# AI 教学助手前端重设计 — 设计规格

## 概述

对 AI 教学助手前端进行视觉重设计，保持现有功能和 API 接口不变，仅替换 CSS 样式和页面布局结构。

## 设计系统

### 配色方案

| Token | 值 | 用途 |
|---|---|---|
| bg-primary | `#0f172a` | 主背景 |
| bg-sidebar | `#0c1525` | 侧边栏背景 |
| bg-surface | `#1e293b` | 卡片/面板背景 |
| bg-surface-hover | `#253349` | 卡片悬停 |
| bg-input | `#0f172a` | 输入框背景 |
| border-default | `#334155` | 默认边框 |
| border-subtle | `rgba(148,163,184,0.1)` | 微边框 |
| text-primary | `#e2e8f0` | 主文字 |
| text-secondary | `#94a3b8` | 次要文字 |
| text-muted | `#64748b` | 弱化文字 |
| accent-blue | `#3b82f6` | 主强调色 |
| accent-purple | `#8b5cf6` | 副强调色 |
| accent-gradient | `#3b82f6 → #8b5cf6` | 渐变强调 |
| user-bubble | `#2563eb` | 用户消息气泡 |
| assistant-bubble | `#1e293b` | AI 消息气泡 |

### 布局结构

侧边栏 + 内容区的经典后台布局：

```
┌──────────┬────────────────────────────────┐
│          │                                │
│  Logo    │        Page Header             │
│  ──────  │                                │
│  Nav     │                                │
│  Nav     │     Content Area                │
│  Nav     │                                │
│  Nav     │                                │
│  ──────  │                                │
│  User    │                                │
└──────────┴────────────────────────────────┘
```

- 侧边栏：200px 固定宽度，`#0c1525` 背景
- 内容区：flex-1 自适应，最大宽度 1200px 居中
- 全局 min-height: 100vh

### 组件规范

**卡片 (Card)**
- `background: linear-gradient(180deg, #1e293b, #1a2332)`
- `border: 1px solid #334155`
- `border-radius: 16px`
- `padding: 20px`

**按钮 (Button)**
- 主按钮：`background: linear-gradient(135deg, #3b82f6, #2563eb)`，白色文字
- 次按钮：`border: 1px solid #334155`，`background: #1e293b`
- 危险按钮：`background: #dc2626`
- `border-radius: 10px`，padding: `10px 20px`

**输入框 (Input/Select/Textarea)**
- `background: #0f172a`
- `border: 1px solid #334155`
- `border-radius: 10px`
- focus: `border-color: #3b82f6`

**聊天气泡**
- 用户：`background: #2563eb`，右对齐，`border-radius: 14px 14px 4px 14px`
- AI：`background: #1e293b`，左对齐，`border-radius: 14px 14px 14px 4px`，带 `border: 1px solid #334155`

**统计数值**
- 使用渐变色：`background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text`

### 字体

- 系统字体栈：`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif`
- 等宽（日志）：`"SF Mono", "Fira Code", "Consolas", monospace`

## 页面设计

### 1. 全局布局 (layout.tsx)

- 侧边栏固定左侧
- 顶栏移除（导航移入侧栏）
- 内容区右侧 scrollable

### 2. 登录页 (/login)

- 居中卡片，max-width: 420px
- 卡片内：Logo + 标题 + 表单
- 背景保持全屏暗色

### 3. 首页 (/)

- 顶部：Hero 区域，渐变标题
- 统计卡片行：用户数、教材数、问答数
- 快速入口卡片：教师端、学生端

### 4. 学生问答页 (/student)

- 左侧面板（240px）：课程下拉、回答模式选择（4 个选项）
- 右侧：对话区 + 底部输入框
- 对话区可滚动，max-height 自适应
- 流式输出时自动滚到底部

### 5. 教师教材管理页 (/teacher)

- 左侧面板：上传表单（学科、年级、作者、文件选择）
- 右侧：教材列表 + 删除管理
- 上传结果卡片内联显示

### 6. 管理员页 (/admin)

- 顶部：系统概览卡片行
- 左侧：账号创建 + 重置密码
- 右侧：日志查看

### 7. 运行指标页 (/metrics)

- 指标卡片行：总数、成功数、成功率、平均耗时
- 工具调用次数列表

## 实现范围

### 不改变
- 所有 TypeScript 业务逻辑（API 调用、状态管理、SSE 解析、路由守卫）
- API 接口和数据结构
- 组件 props 和函数签名

### 改变
- `globals.css` → 完全重写，基于新设计系统
- `layout.tsx` → 从水平顶栏改为侧边栏布局
- `nav-client.tsx` → 从水平导航改为侧边栏导航
- 所有页面组件的 JSX 结构 → 保持逻辑，调整布局嵌套

## 文件变更清单

| 文件 | 变更 |
|---|---|
| `frontend/app/globals.css` | 完全重写 |
| `frontend/app/layout.tsx` | 改为侧边栏结构 |
| `frontend/app/components/nav-client.tsx` | 改为侧边栏组件 |
| `frontend/app/page.tsx` | 调整首页布局 |
| `frontend/app/login/page.tsx` | 调整登录页布局 |
| `frontend/app/student/page.tsx` | 改为左右双栏 |
| `frontend/app/teacher/page.tsx` | 改为左右双栏 |
| `frontend/app/admin/page.tsx` | 调整布局 |
| `frontend/app/metrics/page.tsx` | 调整布局 |
