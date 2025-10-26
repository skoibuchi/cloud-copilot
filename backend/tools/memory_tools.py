from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime


@dataclass
class Context:
    user_id: str


@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """
    Look up user info from agent memory.
    エージェントのメモリからユーザーの情報を検索する
    """
    store = runtime.store
    user_id = runtime.context.user_id
    user_info = store.get(("users",), user_id) 
    return str(user_info.value) if user_info else "Unknown user"


@tool
def save_user_info(user_info: dict, runtime: ToolRuntime[Context]) -> str:
    """
    Save user info to agent memory.
    エージェントのメモリにユーザー情報を保村する
    """
    store = runtime.store
    user_id = runtime.context.user_id
    store.put(("users",), user_id, user_info)
    return "Successfully saved user info."


def get_memory_tools():
    return [
        get_user_info,
        save_user_info
    ]
