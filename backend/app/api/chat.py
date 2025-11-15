from fastapi import APIRouter, Depends, Form, File, UploadFile
from typing import List, Optional
from fastapi.responses import JSONResponse
from app.tools.memory_tools import Context
from app.api.deps import get_current_user
from app.agents.factory import build_agent_for_user
from app.services.file_service import FileService
from app.core.audit import AuditService

router = APIRouter(prefix="/chat", tags=["chat"])
file_sesrvice = FileService()
audit_service = AuditService()


@router.post("/")
async def chat(
    query: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id

    agent_info = build_agent_for_user(user_id)
    agent = agent_info["agent"]
    rag_tool_instance = agent_info.get("rag_tool")

    reply = ""

    # files handling: save and optionally add to vectorstore
    if files and rag_tool_instance:
        try:
            file_paths = await file_sesrvice.save_files(files)
            file_sesrvice.add_to_vectorstore(file_paths, rag_tool_instance)
            reply += "Files uploaded and added to RAG."
            audit_service.log(user_id=user_id, action="app.api.chat.upload_files", resource=str([f.filename for f in files]))
        except Exception as e:
            audit_service.log(user_id=user_id, action="app.api.chat.upload_files", resource=str([f.filename for f in files]),
                              success=False, error_message=str(e), log_level="ERROR")

    if query:
        try:
            response = await agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": query}],
                },
                # you can supply context if your Context class is in memory_tools
                context=Context(user_id=user_id)
            )
            reply = response.get("output", str(response)) if isinstance(response, dict) else str(response)
            audit_service.log(user_id=user_id, action="app.api.chat.query_ai", resource=query,
                              details={"query": query, "reply": reply})
        except Exception as e:
            audit_service.log(user_id=user_id, action="app.api.chat.query_ai", resource=query,
                              success=False, error_message=str(e), log_level="ERROR",
                              details={"query": query, "reply": reply})

    return JSONResponse({"reply": reply})
