"""
Legacy Streamlit entrypoint (deprecated).

Current stack is FastAPI backend + Next.js frontend.
This file is kept temporarily only for migration reference.
"""

import os
import time

import streamlit as st

from utils.metrics import summarize_metrics

from agent.react_agent import ReactAgent
from rag.vector_store import VectorStoreService

st.set_page_config(page_title="AI教学助手", page_icon="📘", layout="wide")
st.title("AI教学助手（教师端 + 学生端）")
st.caption("教师可上传教材 PDF 构建检索知识库，学生端可基于教材进行问答并展示来源。")
st.divider()

api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
if not api_key:
    st.warning(
        "检测到未设置 DASHSCOPE_API_KEY。\n"
        "请在 PowerShell 设置后再启动：$env:DASHSCOPE_API_KEY='你的apikey'"
    )

if "vector_store" not in st.session_state:
    st.session_state["vector_store"] = VectorStoreService()
    st.session_state["vector_store"].load_document()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "你好，我是你的AI教学助手。你可以问我教材里的知识点、例题与解题思路。",
        }
    ]


def load_subject_options() -> list[str]:
    try:
        records = st.session_state["vector_store"].vector_store.get(include=["metadatas"])
        metadatas = records.get("metadatas", []) if records else []
        subjects = sorted({m.get("subject") for m in metadatas if m and m.get("subject")})
        return ["全部"] + subjects if subjects else ["全部"]
    except Exception:
        return ["全部"]

teacher_tab, student_tab, metrics_tab = st.tabs(["教师端：教材入库", "学生端：教学问答", "运行指标"])

with teacher_tab:
    st.subheader("上传教材 PDF 到知识库")

    col1, col2, col3 = st.columns(3)
    with col1:
        subject = st.text_input("学科", value="计算机网络", help="支持自定义，如：计算机网络、操作系统、线性代数")
    with col2:
        grade = st.selectbox("年级", ["大一", "大二", "大三", "大四", "研一", "研二", "其他"])
    with col3:
        author = st.text_input("教材作者", value="未填写", help="可填写一位或多位作者名")

    uploaded_files = st.file_uploader(
        "可一次选择多个教材文件（PDF）",
        type=["pdf"],
        accept_multiple_files=True,
        help="支持上下册或配套习题册同时上传。",
    )

    if st.button("开始入库", type="primary", disabled=not uploaded_files):
        success_count = 0
        duplicate_count = 0
        empty_count = 0
        failed_count = 0
        chunk_count = 0
        metadata = {
            "subject": (subject.strip() or "未分类"),
            "grade": grade,
            "author": (author.strip() or "未分类"),
        }

        try:
            with st.spinner("正在处理教材并写入知识库..."):
                for up_file in uploaded_files or []:
                    data = up_file.read()
                    inserted, status = st.session_state["vector_store"].ingest_uploaded_pdf_bytes_with_status(
                        up_file.name,
                        data,
                        metadata=metadata,
                    )
                    if status == "inserted":
                        success_count += 1
                        chunk_count += inserted
                    elif status == "duplicate":
                        duplicate_count += 1
                    elif status == "empty_content":
                        empty_count += 1
                    else:
                        failed_count += 1

            st.success(
                f"入库完成：新增 {success_count} 个文件，共新增 {chunk_count} 个文本分片。"
                f"（学科：{metadata['subject']}，年级：{metadata['grade']}，作者：{metadata['author']}）"
            )
            if duplicate_count > 0:
                st.info(f"重复文件：{duplicate_count} 个（内容已存在，自动跳过）")
            if empty_count > 0:
                st.warning(f"空内容/不可解析文件：{empty_count} 个（常见于扫描版PDF未做OCR）")
            if failed_count > 0:
                st.error(f"处理失败文件：{failed_count} 个，请查看日志定位原因")
        except ValueError as e:
            err_text = str(e)
            if "InvalidApiKey" in err_text or "401" in err_text:
                st.error(
                    "入库失败：通义 API Key 无效或未生效。请在当前终端设置 DASHSCOPE_API_KEY 后重试。\n"
                    "PowerShell 示例：$env:DASHSCOPE_API_KEY='你的apikey'"
                )
            else:
                st.error(f"入库失败：{err_text}")
        except Exception as e:
            st.error(f"入库失败：{str(e)}")

with student_tab:
    st.subheader("教材问答")

    subject_options = load_subject_options()
    ask_subject = st.selectbox("课程（学科）", subject_options)

    for message in st.session_state["messages"]:
        st.chat_message(message["role"]).write(message["content"])

    query = st.chat_input("请输入你想问的问题，例如：请解释TCP三次握手并给一道例题")

    if query:
        st.chat_message("user").write(query)
        st.session_state["messages"].append({"role": "user", "content": query})

        full_query = f"【课程】{ask_subject}\n【问题】{query}"

        try:
            with st.spinner("教学助手思考中..."):
                answer_chunks = list(st.session_state["agent"].execute_stream(full_query))
                answer = "".join(answer_chunks).strip()
                filtered_lines = []
                seen_lines = set()
                for line in answer.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("【课程】") or stripped.startswith("【问题】"):
                        continue
                    low = stripped.lower()
                    if "tool" in low:
                        continue
                    if "我将基于此进行查询" in stripped:
                        continue
                    if "根据工具" in stripped or "调用工具" in stripped:
                        continue
                    # 去除逐行重复，降低流式拼接导致的重复段落
                    if stripped in seen_lines:
                        continue
                    seen_lines.add(stripped)
                    filtered_lines.append(stripped)
                answer = "\n".join(filtered_lines).strip() or "抱歉，我暂时无法生成有效回答，请换个问法再试。"
        except ValueError as e:
            err_text = str(e)
            if "InvalidApiKey" in err_text or "401" in err_text:
                st.error(
                    "问答失败：通义 API Key 无效或未生效。请检查 DASHSCOPE_API_KEY 后重试。"
                )
            else:
                st.error(f"问答失败：{err_text}")
            st.stop()
        except Exception as e:
            st.error(f"问答失败：{str(e)}")
            st.stop()

        response_chunks = []

        def stream_text(text: str):
            for char in text:
                response_chunks.append(char)
                time.sleep(0.005)
                yield char

        with st.chat_message("assistant"):
            st.write_stream(stream_text(answer))

        st.session_state["messages"].append({"role": "assistant", "content": "".join(response_chunks)})
        st.rerun()

with metrics_tab:
    st.subheader("运行指标（近500条事件）")
    m = summarize_metrics(limit=500)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总问答数", m["total_queries"])
    c2.metric("成功问答数", m["success_queries"])
    c3.metric("问答成功率", f"{m['success_rate']:.1f}%")
    c4.metric("平均耗时(ms)", f"{m['avg_latency_ms']:.0f}")

    st.markdown("**工具调用次数**")
    if m["tool_counts"]:
        st.bar_chart(m["tool_counts"])
    else:
        st.caption("暂无工具调用事件")
