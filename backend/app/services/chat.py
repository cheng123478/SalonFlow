"""会话与对话历史的业务逻辑（双层记忆持久化）。

- 会话层：ChatSession 记录一次连续对话的边界与标题。
- 历史层：ChatMessage（chat_history 表）记录会话内的逐条消息。
- 历史加载注入：回答前按 session 取最近 N 条历史，注入模型上下文。
"""
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession


def _new_key() -> str:
    return uuid.uuid4().hex


async def get_session_by_key(
    db: AsyncSession, user_id: int, session_key: str
) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_key == session_key,
            ChatSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    user_id: int,
    title: str = "新对话",
    session_key: str | None = None,
) -> ChatSession:
    session = ChatSession(
        session_key=session_key or _new_key(),
        user_id=user_id,
        title=title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def persist_turn(
    db: AsyncSession,
    session: ChatSession,
    user_text: str,
    assistant_text: str,
) -> None:
    """一轮问答写回 chat_history 表，并刷新会话更新时间。"""
    db.add(ChatMessage(session_id=session.id, role="user", content=user_text))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=assistant_text))
    session.updated_at = datetime.now()
    await db.commit()


async def load_recent_messages(
    db: AsyncSession, session_id: int, limit: int
) -> list[ChatMessage]:
    """历史加载注入：取会话最近 limit 条消息，按时间正序返回。"""
    rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        )
    ).scalars().all()
    return list(reversed(rows))


async def list_sessions(db: AsyncSession, user_id: int) -> list[dict]:
    sessions = (
        (
            await db.execute(
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    if not sessions:
        return []

    ids = [s.id for s in sessions]
    stat_rows = (
        await db.execute(
            select(
                ChatMessage.session_id,
                func.count(ChatMessage.id),
            )
            .where(ChatMessage.session_id.in_(ids))
            .group_by(ChatMessage.session_id)
        )
    ).all()
    counts = {r[0]: r[1] for r in stat_rows}

    out = []
    for s in sessions:
        last = (
            await db.execute(
                select(ChatMessage.content)
                .where(ChatMessage.session_id == s.id)
                .order_by(ChatMessage.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        out.append(
            {
                "id": s.id,
                "session_key": s.session_key,
                "user_id": s.user_id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": counts.get(s.id, 0),
                "last_message": last or "",
            }
        )
    return out


async def list_messages(
    db: AsyncSession, session_id: int
) -> list[ChatMessage]:
    rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
        )
    ).scalars().all()
    return list(rows)


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.execute(
        ChatMessage.__table__.delete().where(ChatMessage.session_id == session.id)
    )
    await db.delete(session)
    await db.commit()