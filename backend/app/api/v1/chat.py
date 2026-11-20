"""Agent 聊天接口：SSE 流式 + RAG 检索 + 双层记忆 + 写操作二次确认。

双层记忆：
- 会话层（chat_session 表）：记录一次连续对话的边界，按 user_id 隔离。
- 历史层（chat_history 表）：会话内逐条消息，回答前按 session 加载注入模型上下文。
"""
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.event import JSONServerSentEvent
from sse_starlette.sse import EventSourceResponse

from app.agent import memory, rag
from app.agent.actions import execute_action
from app.agent.graph import graph
from app.agent.state import AgentState
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import async_session, get_db
from app.core.response import success
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.chat import MessageOut
from app.services import chat as service

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
    dependencies=[Depends(get_current_user)],
)


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None


class ExecuteIn(BaseModel):
    action: str
    params: dict


def _to_lc_messages(rows: list) -> list:
    """把 chat_history 记录转换为 LangChain 消息（历史加载注入）。"""
    return [
        AIMessage(content=r.content) if r.role == "assistant" else HumanMessage(content=r.content)
        for r in rows
    ]


def _fallback_answer(results: list[dict]) -> str:
    """未配置回答模型时，直接把检索片段整理成回答。"""
    if not results:
        return "当前门店知识库中没有检索到相关内容，请换一种更具体的问法。"
    parts = ["根据门店知识库检索，相关信息如下："]
    for r in results[:3]:
        title = r.get("title", "门店知识")
        text = (r.get("text") or "").strip()
        if len(text) > 430:
            text = text[:430] + "……"
        parts.append(f"\n- {title}：{text}")
    return "".join(parts)


@router.post("/chat")
async def chat(
    body: ChatIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id

    # 解析会话：已有则复用，否则新建（便于跨请求延续上下文）
    session = None
    if body.session_id:
        session = await service.get_session_by_key(db, user_id, body.session_id)
    if session is None:
        title = body.message.strip()[:30] or "新对话"
        session = await service.create_session(
            db, user_id, title=title, session_key=body.session_id
        )

    session_key = session.session_key

    # 历史加载注入：取最近 N 条历史拼进上下文
    history_rows = await service.load_recent_messages(
        db, session.id, settings.history_limit
    )
    history_messages = _to_lc_messages(history_rows)

    # 未配置大模型：直接检索知识库并整理片段返回（降级兜底）
    if not settings.deepseek_api_key:
        try:
            results = await rag.search(body.message, top_k=4)
        except Exception:
            results = []
        answer = _fallback_answer(results)
        await service.persist_turn(db, session, body.message, answer)

        async def fallback_gen():
            yield JSONServerSentEvent(data={"type": "token", "content": answer})
            yield JSONServerSentEvent(data={
                "type": "done",
                "answer": answer,
                "session_id": session_key,
                "pending_action": None,
                "sources": [rag.to_source(r) for r in results],
            })

        return EventSourceResponse(fallback_gen())

    # 长期记忆召回：按当前用户检索最相关记忆，注入上下文
    memory_context = memory.format_memories(
        await memory.recall_memories(user_id, body.message)
    )

    # 正常路径：交给 LangGraph
    inputs: AgentState = {
        "messages": history_messages + [HumanMessage(content=body.message)],
        "plan": "",
        "tool_result": "",
        "pending_action": None,
        "rag_context": "",
        "sources": [],
        "answer": "",
        "memory_context": memory_context,
    }

    async def event_generator():
        final_state: AgentState = inputs
        answer = ""
        try:
            async for event in graph.astream(inputs, stream_mode=["messages", "values"]):
                mode, payload = event
                if mode == "messages":
                    chunk, metadata = payload
                    node = metadata.get("langgraph_node") if isinstance(metadata, dict) else None
                    content = getattr(chunk, "content", None) if node == "responder" else None
                    if content:
                        if not isinstance(content, str):
                            content = str(content)
                        yield JSONServerSentEvent(data={"type": "token", "content": content})
                elif mode == "values":
                    final_state = payload
            answer = final_state.get("answer", "")
        except Exception as exc:  # noqa: BLE001
            yield JSONServerSentEvent(data={"type": "error", "message": f"Agent 执行失败：{exc}"})

        # 回答成功后写回双层记忆（用独立会话，避免流式期间依赖会话已关闭）
        if answer:
            async with async_session() as write_db:
                session_ref = await write_db.get(ChatSession, session.id)
                if session_ref is not None:
                    await service.persist_turn(
                        write_db, session_ref, body.message, answer
                    )

        # 长期记忆沉淀：抽取本轮值得记住的事实并写入（best-effort，失败不阻塞回复）
        if answer:
            try:
                mems = await memory.extract_memories(body.message, answer)
                await memory.remember_memories(user_id, mems)
            except Exception:
                pass

        yield JSONServerSentEvent(data={
            "type": "done",
            "answer": answer,
            "session_id": session_key,
            "pending_action": final_state.get("pending_action"),
            "sources": final_state.get("sources") or [],
        })

    return EventSourceResponse(event_generator())


@router.post("/execute")
async def execute(body: ExecuteIn, db: AsyncSession = Depends(get_db)):
    try:
        await execute_action(db, body.action, body.params)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"参数不完整或格式错误：{exc}")
    return success(message="执行成功")


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await service.list_sessions(db, current_user.id)
    return success(items)


@router.get("/sessions/{session_key}/messages")
async def list_messages(
    session_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await service.get_session_by_key(db, current_user.id, session_key)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = await service.list_messages(db, session.id)
    return success([MessageOut.model_validate(m).model_dump() for m in messages])


@router.delete("/sessions/{session_key}")
async def delete_session(
    session_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await service.get_session_by_key(db, current_user.id, session_key)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    await service.delete_session(db, session)
    return success(message="删除成功")