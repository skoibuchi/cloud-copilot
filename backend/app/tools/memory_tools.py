from dataclasses import dataclass
from typing import Optional, Dict
from langchain.tools import tool, ToolRuntime
from app.database.database import SessionLocal
from app.services.cloud_config_service import get_configs_dict


# ----------------------------
# Runtime Context
# ----------------------------
@dataclass
class Context:
    """
    Context for the agent runtime.
    エージェント実行時のコンテキスト
    """
    user_id: int
    credentials: Optional[Dict] = None  # Cloud credentials will be stored here
    user_info: Optional[dict] = None    # User info can be stored here


# ----------------------------
# User Info Tools
# ----------------------------
@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """
    Look up user info from agent memory.
    エージェントのメモリからユーザー情報を検索する
    """
    store = runtime.store
    user_id = runtime.context.user_id
    user_info = store.get(("users",), user_id)
    runtime.context.user_info = user_info.value if user_info else None
    return str(runtime.context.user_info) if runtime.context.user_info else "Unknown user"


@tool
def save_user_info(user_info: dict, runtime: ToolRuntime[Context]) -> str:
    """
    Save user info to agent memory.
    エージェントのメモリにユーザー情報を保存する
    """
    store = runtime.store
    user_id = runtime.context.user_id
    store.put(("users",), user_id, user_info)
    runtime.context.user_info = user_info
    return "Successfully saved user info."


# ----------------------------
# Cloud Credentials Tools
# ----------------------------
@tool
def load_user_cloud_credentials(runtime: ToolRuntime[Context]) -> str:
    """
    Load cloud credentials for the user from DB and store in runtime context.
    DBからユーザーのクラウド認証情報をロードして runtime.context.credentials に格納
    """
    user_id = runtime.context.user_id
    db = SessionLocal()
    creds = get_configs_dict(db=db, user_id=user_id)
    db.close()
    runtime.context.credentials = creds
    return "Cloud credentials loaded."


@tool
def get_cloud_credentials(runtime: ToolRuntime[Context], provider: str, region: Optional[str] = None) -> dict:
    """
    Retrieve credentials for a specific cloud provider (and optional region) from context.
    runtime.context から指定クラウド・リージョンの認証情報を取得
    """
    creds_dict = runtime.context.credentials or {}
    provider_entries = creds_dict.get(provider, [])
    if region:
        entry = next((e for e in provider_entries if e.get("region") == region), None)
    else:
        entry = provider_entries[0] if provider_entries else None
    return entry.get("credentials") if entry else {}


# ----------------------------
# Exported Tools
# ----------------------------
def get_memory_tools():
    """
    Return all memory-related tools.
    メモリ関連のツールをまとめて返す
    """
    return [
        get_user_info,
        save_user_info,
        load_user_cloud_credentials,
        get_cloud_credentials
    ]
