import os
import re

import pandas as pd
import requests
from langchain_core.tools import tool
from pypdf import PdfReader

from rag.rag_service import RagSummarizeService
from rag.vector_store import VectorStoreService
from utils.config_handler import agent_conf
from utils.path_tools import get_abs_path

vector_store = VectorStoreService()
rag = RagSummarizeService(vector_store)


@tool(description="从向量存储中检索课程参考资料，并返回答案与来源页码")
def rag_summarize(query: str) -> str:
    result = rag.answer_with_citations(query)
    answer = (result.get("answer", "") or "").strip()
    sources = result.get("sources", [])

    # 清理模型可能自行生成的“参考页码/参考来源”尾部，避免重复输出与二次复述
    answer = re.split(r"\n\s*参考(?:页码|来源)\s*[：:]", answer, maxsplit=1)[0].strip()

    if not sources:
        return answer

    # 仅输出最终命中的页码，去重并保持顺序
    pages = []
    seen = set()
    for src in sources[:3]:
        page = str(src.get("page", "")).strip()
        if not page or page in seen:
            continue
        seen.add(page)
        pages.append(page)

    if not pages:
        return answer

    return f"{answer}\n\n参考页码：{'、'.join(pages)}"


def _normalize_course_name(course: str, columns: list[str]) -> str:
    course = (course or "").strip()
    alias_map = {
        "计网": "计算机网络",
        "计算机网络": "计算机网络",
        "高数": "数学",
        "大学英语": "英语",
    }

    mapped = alias_map.get(course, course)
    if mapped in columns:
        return mapped

    for col in columns:
        if mapped and (mapped in col or col in mapped):
            return col
    return mapped


@tool(description="学生成绩查询工具。metric支持average/max/rank/fail_count/above；course填写课程名；rank可选student_name；above可选threshold")
def query_student_scores(metric: str, course: str, student_name: str = "", threshold: str = "") -> str:
    csv_path = get_abs_path(agent_conf.get("student_score_data_path", "data/external/student_scores.csv"))
    if not os.path.exists(csv_path):
        return "成绩数据暂不可用。"

    df = pd.read_csv(csv_path)
    if "姓名" not in df.columns:
        return "成绩表缺少“姓名”列。"

    score_columns = [c for c in df.columns if c != "姓名"]
    course = _normalize_course_name(course, score_columns)

    if course not in df.columns:
        return f"未找到课程“{course}”，可用课程：{', '.join(score_columns)}"

    metric = metric.lower().strip()

    if metric == "average":
        avg = float(df[course].mean())
        return f"课程【{course}】平均分为 {avg:.2f}。"

    if metric == "max":
        idx = df[course].idxmax()
        row = df.loc[idx]
        return f"课程【{course}】最高分是 {row[course]}，学生是 {row['姓名']}。"

    if metric == "fail_count":
        fail_cnt = int((df[course] < 60).sum())
        return f"课程【{course}】不及格（<60分）人数为 {fail_cnt} 人。"

    if metric == "above":
        try:
            line = float(threshold)
        except Exception:
            return "分数线参数无效。"

        selected = df[df[course] >= line][["姓名", course]].sort_values(by=course, ascending=False)
        if selected.empty:
            return f"课程【{course}】分数≥{line:.0f} 的学生人数为 0 人。"

        names = "，".join(selected["姓名"].tolist())
        return f"课程【{course}】分数≥{line:.0f} 的学生人数为 {len(selected)} 人，分别是：{names}。"

    if metric == "rank":
        ranked = df[["姓名", course]].sort_values(by=course, ascending=False).reset_index(drop=True)
        ranked["排名"] = ranked.index + 1

        if student_name:
            target = ranked[ranked["姓名"] == student_name]
            if target.empty:
                return f"未找到学生“{student_name}”。"
            rec = target.iloc[0]
            return f"学生{student_name}在【{course}】的排名是第{int(rec['排名'])}，分数为{rec[course]}。"

        top5 = ranked.head(5)
        return "\n".join([f"第{int(r['排名'])}名 {r['姓名']}：{r[course]}" for _, r in top5.iterrows()])

    return "metric参数无效，请使用 average / max / rank / fail_count / above。"


@tool(description="复合成绩分析工具。可在一次调用中统计平均分、挂科人数、分数线以上人数与名单。")
def analyze_student_scores(course: str, query: str) -> str:
    csv_path = get_abs_path(agent_conf.get("student_score_data_path", "data/external/student_scores.csv"))
    if not os.path.exists(csv_path):
        return "成绩数据暂不可用。"

    df = pd.read_csv(csv_path)
    if "姓名" not in df.columns:
        return "成绩表缺少“姓名”列。"

    score_columns = [c for c in df.columns if c != "姓名"]
    course = _normalize_course_name(course, score_columns)
    if course not in df.columns:
        return f"未找到课程“{course}”，可用课程：{', '.join(score_columns)}"

    parts = []
    q = query or ""

    if any(k in q for k in ["平均", "平均分"]):
        avg = float(df[course].mean())
        parts.append(f"平均分：{avg:.2f}")

    if any(k in q for k in ["挂科", "不及格"]):
        fail_cnt = int((df[course] < 60).sum())
        parts.append(f"挂科人数（<60分）：{fail_cnt}人")

    if any(k in q for k in ["最高分", "最高"]):
        idx = df[course].idxmax()
        row = df.loc[idx]
        parts.append(f"最高分：{row[course]}（{row['姓名']}）")

    m = re.search(r"(\d+)\s*分\s*(以上|及以上)", q)
    if m:
        line = float(m.group(1))
        selected = df[df[course] >= line][["姓名", course]].sort_values(by=course, ascending=False)
        if selected.empty:
            parts.append(f"{int(line)}分及以上：0人")
        else:
            names = "，".join(selected["姓名"].tolist())
            parts.append(f"{int(line)}分及以上：{len(selected)}人（{names}）")

    if not parts:
        avg = float(df[course].mean())
        parts.append(f"平均分：{avg:.2f}")

    return f"课程【{course}】成绩统计：" + "；".join(parts) + "。"


@tool(description="技术问答搜索工具。用于Python报错、框架问题、技术文档检索。")
def search_tech_qa(query: str, top_k: int = 5) -> str:
    bing_key = os.getenv("BING_SEARCH_API_KEY", "").strip()

    if bing_key:
        try:
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": bing_key}
            params = {"q": query, "count": top_k, "mkt": "zh-CN"}
            resp = requests.get(endpoint, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("webPages", {}).get("value", [])
            if not items:
                return "未检索到相关技术结果。"
            return "\n".join(
                [f"- {it.get('name', '')}\n  {it.get('snippet', '')}\n  {it.get('url', '')}" for it in items[:top_k]]
            )
        except Exception:
            pass

    try:
        ddg_url = f"https://duckduckgo.com/?q={query}&format=json&pretty=1"
        resp = requests.get(ddg_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        lines = []
        abstract = data.get("AbstractText", "")
        if abstract:
            lines.append(f"摘要：{abstract}")

        for item in data.get("RelatedTopics", [])[:top_k]:
            if isinstance(item, dict):
                text = item.get("Text")
                url = item.get("FirstURL", "")
                if text:
                    lines.append(f"- {text}\n  {url}")

        return "\n".join(lines) if lines else "未检索到相关技术结果。"
    except Exception as e:
        return f"技术搜索失败：{str(e)}"


@tool(description="读取用户上传文件并按问题返回相关片段。支持txt/pdf。")
def query_uploaded_file(filename: str, question: str) -> str:
    base_dir = get_abs_path(agent_conf.get("uploaded_files_path", "data/uploads"))
    file_path = os.path.join(base_dir, filename)

    if not os.path.exists(file_path):
        return f"未找到上传文件：{filename}"

    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    elif file_path.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        content = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        return "暂不支持该文件类型，仅支持txt/pdf。"

    if not content.strip():
        return "文件内容为空或无法解析。"

    keywords = [k for k in question.replace("，", " ").replace("。", " ").split() if k]
    snippets = []

    for line in content.splitlines():
        if any(k in line for k in keywords):
            snippets.append(line.strip())
        if len(snippets) >= 8:
            break

    if not snippets:
        return "文件中未检索到与问题直接相关的片段。"

    return "\n".join(snippets)
