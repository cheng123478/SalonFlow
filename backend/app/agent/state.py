"""Agent 共享状态定义（LangGraph StateGraph 的状态）。"""
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """一次 Agent 对话的运行状态。

    - messages: 累积的对话消息（add_messages 自动合并）。
    - plan: planner 节点产出的任务计划（当前为轻量记录，后续可增强）。
    - tool_result: tool_executor 节点执行只读工具后的结果摘要。
    - pending_action: 需要用户二次确认的写操作 {"action": str, "params": dict}，无则为 None。
    - rag_context: RAG 检索到的知识片段（rag_retriever 节点产出）。
    - sources: RAG 检索结果结构化为参考来源列表 [{title, score, excerpt}]。
    - answer: responder 节点产出的最终回复。
    - memory_context: 长期记忆召回文本（进入图前由 chat 接口注入，responder 拼进提示词）。
    """

    messages: Annotated[list[BaseMessage], add_messages]
    plan: str
    tool_result: str
    pending_action: dict | None
    rag_context: str
    sources: list[dict]
    answer: str
    memory_context: str
