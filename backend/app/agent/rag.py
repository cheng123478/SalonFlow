"""RAG：SiliconFlow bge-m3 向量化 + Qdrant 向量检索。

说明：直连 Qdrant REST API（httpx）而非 qdrant-client / langchain-qdrant，
因为后两者与当前环境的 pydantic 2.14 / openai 3.x 存在依赖冲突。
"""
import re
import uuid

import httpx

from app.core.config import settings

EMBED_DIM = 1024  # BAAI/bge-m3 输出维度
COLLECTION = "salonflow_knowledge"
EMBED_URL = settings.embedding_base_url.rstrip("/") + "/embeddings"
QDRANT_URL = settings.qdrant_url.rstrip("/")


def _embed_headers() -> dict:
    return {"Authorization": f"Bearer {settings.embedding_api_key}"}


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 SiliconFlow bge-m3 批量向量化。"""
    if not texts:
        return []
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            EMBED_URL,
            json={"model": settings.embedding_model, "input": texts},
            headers=_embed_headers(),
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]


async def ensure_collection(name: str = COLLECTION) -> None:
    """确保集合存在（不存在则创建，1024 维余弦相似度）。"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{QDRANT_URL}/collections/{name}")
        if r.status_code == 200:
            return
        r = await client.put(
            f"{QDRANT_URL}/collections/{name}",
            json={"vectors": {"size": EMBED_DIM, "distance": "Cosine"}},
        )
        r.raise_for_status()


async def ingest_texts(
    texts: list[str],
    metadatas: list[dict] | None = None,
    collection: str = COLLECTION,
) -> int:
    """向量化并写入指定 Qdrant 集合，返回写入条数。"""
    if not texts:
        return 0
    await ensure_collection(collection)
    vectors = await embed_texts(texts)
    metadatas = metadatas or [{} for _ in texts]
    points = [
        {
            "id": str(uuid.uuid4()),
            "vector": vec,
            "payload": {"text": text, "chunk_index": i, **(meta or {})},
        }
        for i, (vec, text, meta) in enumerate(zip(vectors, texts, metadatas))
    ]
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(
            f"{QDRANT_URL}/collections/{collection}/points?wait=true",
            json={"points": points},
        )
        resp.raise_for_status()
    return len(points)


async def search(
    query: str,
    top_k: int = 4,
    collection: str = COLLECTION,
    filter: dict | None = None,
) -> list[dict]:
    """向量检索，返回 [{text, score, ...metadata}]（按相似度降序）。可按 collection / filter 过滤。"""
    await ensure_collection(collection)
    vector = (await embed_texts([query]))[0]
    body: dict = {"vector": vector, "limit": top_k, "with_payload": True}
    if filter is not None:
        body["filter"] = filter
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{QDRANT_URL}/collections/{collection}/points/search",
            json=body,
        )
        resp.raise_for_status()
        hits = resp.json()["result"]
    out = []
    for h in hits:
        payload = h.get("payload", {})
        text = payload.get("text", "")
        meta = {k: v for k, v in payload.items() if k != "text"}
        out.append({"text": text, "score": h.get("score"), **meta})
    return out


def chunk_text(text: str, max_len: int = 500) -> list[str]:
    """按段落切块（尽量在换行处断开，超长再按长度硬切）。"""
    text = text.strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    chunks = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 1 <= max_len:
            buf = (buf + "\n" + p) if buf else p
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    final = []
    for c in chunks:
        while len(c) > max_len:
            final.append(c[:max_len])
            c = c[max_len:]
        if c:
            final.append(c)
    return final


def format_hits(hits: list[dict]) -> str:
    """把检索结果格式化为给大模型的文本。"""
    if not hits:
        return "知识库中没有找到相关内容。"
    lines = [f"知识库检索到 {len(hits)} 条相关内容："]
    for i, h in enumerate(hits, 1):
        src = h.get("title") or ""
        suffix = f"（来源：{src}）" if src else ""
        lines.append(f"{i}. {h['text']}{suffix}")
    return "\n".join(lines)


def to_source(hit: dict) -> dict:
    """把单条检索结果转为前端的参考来源结构。"""
    return {
        "title": hit.get("title", "门店知识"),
        "score": round(float(hit.get("score", 0)), 4),
        "excerpt": (hit.get("text") or "")[:120],
    }


async def list_documents(limit: int = 1000) -> list[dict]:
    """列出知识库文档（按标题聚合分块，返回 [{title, chunks}]）。"""
    await ensure_collection()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
            json={"limit": limit, "with_payload": True},
        )
        resp.raise_for_status()
        points = resp.json()["result"]["points"]
    docs: dict[str, int] = {}
    for p in points:
        title = (p.get("payload") or {}).get("title") or "未命名"
        docs[title] = docs.get(title, 0) + 1
    return [{"title": t, "chunks": c} for t, c in docs.items()]


async def delete_document(title: str) -> None:
    """按标题删除一篇知识文档（含其全部分块）。"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/delete",
            json={"filter": {"must": [{"key": "title", "match": {"value": title}}]}},
        )
        resp.raise_for_status()


async def get_document(title: str) -> dict | None:
    """按标题取回一篇文档（按 chunk_index 顺序还原原始内容）。"""
    await ensure_collection()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
            json={
                "filter": {"must": [{"key": "title", "match": {"value": title}}]},
                "limit": 1000,
                "with_payload": True,
            },
        )
        resp.raise_for_status()
        points = resp.json()["result"]["points"]
    if not points:
        return None
    points = sorted(points, key=lambda p: (p.get("payload") or {}).get("chunk_index", 0))
    content = "\n".join((p.get("payload") or {}).get("text", "") for p in points)
    return {"title": title, "content": content}
