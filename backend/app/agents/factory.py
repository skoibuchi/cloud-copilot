from functools import lru_cache
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore
from app.core.config import settings
from app.llm import get_llm  # your existing llm helper
from app.tools import get_tools  # your existing get_tools
import threading

_user_agent_lock = threading.Lock()
_user_agent_cache = {}  # TODO improve


def build_agent_for_user(user_id: int):
    """
    Build or return cached agent for a given user_id.
    Note: cache invalidation is not implemented here; add TTL or eviction if needed.
    """
    with _user_agent_lock:
        if user_id in _user_agent_cache:
            return _user_agent_cache[user_id]

        llm = get_llm(settings.LLM_PROVIDER)
        tools, rag_tool_instance = get_tools(user=str(user_id), vectorstore_class=settings.VECTORSTORE_CLASS)
        store = InMemoryStore()
        agent = create_agent(tools=tools, llm=llm, store=store)

        _user_agent_cache[user_id] = {
            "agent": agent,
            "rag_tool": rag_tool_instance
        }
        return _user_agent_cache[user_id]
