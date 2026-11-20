"""知识库 API：向量化入库（阶段 5）。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agent import rag
from app.api.deps import get_current_user
from app.core.response import fail, success

router = APIRouter(
    prefix="/knowledge",
    tags=["知识库"],
    dependencies=[Depends(get_current_user)],
)


class KnowledgeIngest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


@router.post("/ingest")
async def ingest_knowledge(body: KnowledgeIngest):
    """把一篇知识文档切块向量化写入 Qdrant。"""
    chunks = rag.chunk_text(body.content)
    if not chunks:
        return success(message="内容为空")
    n = await rag.ingest_texts(chunks, metadatas=[{"title": body.title} for _ in chunks])
    return success({"chunks": n}, "入库成功")


@router.get("/list")
async def list_knowledge():
    """列出知识库中的文档（按标题聚合）。"""
    docs = await rag.list_documents()
    return success(docs)


class KnowledgeDelete(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@router.post("/delete")
async def delete_knowledge(body: KnowledgeDelete):
    """按标题删除一篇知识文档。"""
    await rag.delete_document(body.title)
    return success(message="删除成功")


@router.get("/detail")
async def detail_knowledge(title: str):
    """按标题取回一篇文档的原始内容。"""
    doc = await rag.get_document(title)
    if doc is None:
        return fail(404, "文档不存在")
    return success(doc)


class KnowledgeUpdate(BaseModel):
    old_title: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


@router.post("/update")
async def update_knowledge(body: KnowledgeUpdate):
    """更新一篇知识文档：先删除旧分块，再按新内容重新入库。"""
    await rag.delete_document(body.old_title)
    chunks = rag.chunk_text(body.content)
    if not chunks:
        return success(message="内容为空")
    n = await rag.ingest_texts(chunks, metadatas=[{"title": body.title} for _ in chunks])
    return success({"chunks": n}, "更新成功")
