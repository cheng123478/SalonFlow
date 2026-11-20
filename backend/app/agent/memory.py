"""长期记忆：跨会话沉淀顾客/门店事实与偏好，按 user_id 隔离，Qdrant 向量召回。

- recall_memories：按 user_id 过滤，向量检索与当前提问最相关的记忆。
- remember_memories：去重后把新抽取的事实写入 salonflow_memory 集合。
- extract_memories：每轮对话结束后由 LLM 抽取值得长期记住的事实（输出 JSON 数组）。
"""
import json
import re
from datetime import datetime, timezone

from app.agent import rag
from app.agent.llm import get_llm
from app.core.config import settings

MEMORY_COLLECTION = "salonflow_memory"

# 单轮抽取的最大记忆条数，防止记忆膨胀
MAX_MEMORIES_PER_TURN = 5

EXTRACT_PROMPT = """根据下面这轮对话，抽取值得「长期记住」的事实或偏好（例如顾客偏好、发质/护理习惯、门店经营规则、用户明确表达的偏好）。
规则：
- 每条是一句简洁、可独立理解的中文陈述。
- 只抽取明确、稳定、未来可能再次用到的事实；不要抽取临时性的问答内容。
- 最多抽取 {max} 条；没有值得记住的就输出空数组。
- 只输出一个 JSON 数组，不要输出任何 JSON 以外的内容。

用户：{user}
助手：{assistant}
"""


def _user_filter(user_id: int) -> dict:
    """Qdrant payload 过滤：只匹配当前用户的记忆。"""
    return {"must": [{"key": "user_id", "match": {"value": user_id}}]}


async def recall_memories(user_id: int, query: str, top_k: int | None = None) -> list[dict]:
    """按 user_id 过滤，检索与 query 最相关的长期记忆。失败时返回空列表。"""
    top_k = top_k or settings.memory_top_k
    try:
        return await rag.search(
            query,
            top_k=top_k,
            collection=MEMORY_COLLECTION,
            filter=_user_filter(user_id),
        )
    except Exception:
        return []


def format_memories(hits: list[dict]) -> str:
    """把召回的记忆格式化为注入上下文的文本。"""
    if not hits:
        return ""
    lines = ["以下是关于当前用户/门店的长期记忆（请酌情参考）："]
    for h in hits:
        lines.append(f"- {h['text']}")
    return "\n".join(lines)


async def remember_memories(user_id: int, memories: list[str]) -> int:
    """去重后写入长期记忆，返回实际写入条数。失败返回 0（best-effort）。"""
    if not memories:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    accepted: list[str] = []
    for text in memories:
        text = (text or "").strip()
        if not text:
            continue
        # 去重：与已有记忆做一次相似度检索，命中阈值则跳过
        try:
            dup = await rag.search(
                text,
                top_k=1,
                collection=MEMORY_COLLECTION,
                filter=_user_filter(user_id),
            )
            if dup and dup[0].get("score", 0) >= settings.memory_similarity_threshold:
                continue
        except Exception:
            pass
        accepted.append(text)

    if not accepted:
        return 0

    metadatas = [{"user_id": user_id, "created_at": now} for _ in accepted]
    try:
        return await rag.ingest_texts(
            accepted, metadatas=metadatas, collection=MEMORY_COLLECTION
        )
    except Exception:
        return 0


async def extract_memories(user_text: str, assistant_text: str) -> list[str]:
    """每轮对话后由 LLM 抽取值得长期记住的事实，失败时返回空列表。"""
    try:
        llm = get_llm()
    except RuntimeError:
        return []

    prompt = EXTRACT_PROMPT.format(
        max=MAX_MEMORIES_PER_TURN, user=user_text, assistant=assistant_text
    )
    try:
        resp = await llm.ainvoke(prompt)
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception:
        return []

    items = _parse_json_array(content)
    return [s for s in items if isinstance(s, str) and s.strip()][:MAX_MEMORIES_PER_TURN]


def _parse_json_array(content: str) -> list:
    """尽量鲁棒地把模型输出解析成 JSON 数组。"""
    content = content.strip()
    # 去掉可能的 ```json ... ``` 代码块
    m = re.search(r"\[[\s\S]*\]", content)
    if m:
        content = m.group(0)
    try:
        data = json.loads(content)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    # 某些模型可能包一层 {"memories": [...]}
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []
