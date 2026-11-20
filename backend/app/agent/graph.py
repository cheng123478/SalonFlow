"""LangGraph 状态机：planner / router / tool_executor / responder。"""
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from app.agent import rag
from app.agent.llm import get_llm
from app.agent.prompts import RESPONDER_PROMPT, SYSTEM_PROMPT
from app.agent.state import AgentState
from app.agent.tools import PROPOSE_ACTION_MAP, TOOLS, search_knowledge


async def planner_node(state: AgentState) -> dict:
    """规划节点：记录本轮用户请求（轻量实现，后续可增强为真正的任务规划）。"""
    messages = state.get("messages", [])
    user_text = ""
    for m in reversed(messages):
        if getattr(m, "type", None) == "human":
            user_text = m.content if isinstance(m.content, str) else str(m.content)
            break
    return {"plan": f"处理请求：{user_text[:80]}"}


async def router_node(state: AgentState) -> dict:
    """路由节点：用带工具的 LLM 决定调用哪个工具，或直接进入回复。"""
    llm = get_llm()
    tools = [search_knowledge, *[impl for impl, _ in TOOLS.values()]]
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state.get("messages", [])
    response = await llm.bind_tools(tools).ainvoke(messages)
    return {"messages": [response]}


async def tool_executor_node(state: AgentState) -> dict:
    """工具执行节点：统一执行本轮所有工具调用。

    既处理只读查询/写方案（query_* / propose_*），也处理 search_knowledge（RAG 检索）。
    合并成一个节点，避免一轮里混合调用 search_knowledge + 其它工具时，
    其中一个调用没有对应的 ToolMessage 而触发 OpenAI 400。
    """
    messages = state.get("messages", [])
    tool_calls = getattr(messages[-1], "tool_calls", None) or []

    tool_messages = []
    results = []
    rag_parts = []
    sources = []
    pending_action = None

    for tc in tool_calls:
        name = tc.get("name")
        tool_call_id = tc.get("id")

        if name == "search_knowledge":
            query = (tc.get("args") or {}).get("query", "")
            try:
                hits = await rag.search(query, top_k=4)
                text = rag.format_hits(hits)
                sources = [rag.to_source(h) for h in hits]
            except Exception as exc:  # noqa: BLE001
                text = f"知识库检索失败：{exc}"
            rag_parts.append(text)
            tool_messages.append(ToolMessage(content=text, tool_call_id=tool_call_id))
            continue

        entry = TOOLS.get(name)
        if entry is None:
            tool_messages.append(ToolMessage(content=f"未知工具：{name}", tool_call_id=tool_call_id))
            continue
        impl, is_propose = entry
        try:
            result = await impl.ainvoke(tc.get("args", {}))
        except Exception as exc:  # noqa: BLE001
            result = f"工具执行失败：{exc}"
        results.append(f"[{name}] {result}")
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
        if is_propose:
            pending_action = {"action": PROPOSE_ACTION_MAP[name], "params": tc.get("args", {})}

    return {
        "messages": tool_messages,
        "tool_result": "\n".join(results),
        "rag_context": "\n".join(rag_parts),
        "sources": sources,
        "pending_action": pending_action,
    }


async def responder_node(state: AgentState) -> dict:
    """回复节点：综合工具结果/方案，生成最终回复（用于流式输出）。"""
    llm = get_llm()
    memory_context = state.get("memory_context", "") or ""
    memory_block = f"\n\n{memory_context}" if memory_context else ""
    system = SystemMessage(
        content=SYSTEM_PROMPT + "\n\n" + RESPONDER_PROMPT + memory_block
    )
    messages = [system] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    return {"messages": [response], "answer": content}


def route_after_router(state: AgentState) -> str:
    """router 之后：有工具调用走 tool_executor，否则直接 responder。"""
    messages = state.get("messages", [])
    tool_calls = getattr(messages[-1], "tool_calls", None) if messages else None
    if tool_calls:
        return "tool_executor"
    return "responder"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("router", router_node)
    builder.add_node("tool_executor", tool_executor_node)
    builder.add_node("responder", responder_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "router")
    builder.add_conditional_edges(
        "router",
        route_after_router,
        {"tool_executor": "tool_executor", "responder": "responder"},
    )
    builder.add_edge("tool_executor", "responder")
    builder.add_edge("responder", END)

    return builder.compile()


# 模块级单例：全局复用编译好的图
graph = build_graph()
