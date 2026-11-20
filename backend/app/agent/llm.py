"""LLM 实例：DeepSeek（OpenAI 兼容接口）。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache
def get_llm() -> ChatOpenAI:
    """返回全局复用的 DeepSeek 对话模型。"""
    if not settings.deepseek_api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，无法初始化 Agent 大模型")
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        timeout=60,
    )
