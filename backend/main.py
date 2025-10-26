import os
from fastapi import FastAPI, UploadFile, Form, File, Query
from typing import List, Optional
from fastapi.responses import JSONResponse
from langchain.agents import create_agent
from llm import get_llm
from tools import get_tools
from tools.multi_cloud_tools import list_all_cloud_resources
from dotenv import load_dotenv
load_dotenv()

# Load settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
CLOUD_PROVIDERS = os.getenv("CLOUD_PROVIDERS", "gcp").lower()
VECTORSTORE = os.getenv("VECTORSTORE_CLASS", "chroma").lower()

# Initialize
# Server
app = FastAPI()
# LLM
llm = get_llm(LLM_PROVIDER)
# Tool
tools, rag_tool_instance = get_tools(CLOUD_PROVIDERS, VECTORSTORE)
# Agent
agent = create_agent(tools=tools, llm=llm)


@app.post("/chat")
async def chat(
    query: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Received query, return LLM agent response
    Received files, ave into vectordb

    Args:
        - query: str, user's request
        - files: List[UploadFile], uploaded files
    """
    reply = ""

    # using vectorstore & uploaded files
    if files and rag_tool_instance:
        file_paths = []
        for f in files:
            save_path = f"./temp_uploads/{f.filename}"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as buffer:
                buffer.write(await f.read())
            file_paths.append(save_path)
        reply += rag_tool_instance.add_document(file_paths=file_paths)

    if query:
        response = await agent.ainvoke({"input": query})
        reply = response.get("output", str(response)) if isinstance(response, dict) else str(response)

    return JSONResponse({
        "reply": reply,
        "sources": getattr(response, "artifact", None)
    })


@app.get("/cloud-resources")
async def cloud_resources(providers: Optional[str] = Query(None, description="comma-separated list of cloud providers")):
    """
    Return information of all cloud environment

    Args:
        - providers: str, "aws,azure,gcp,ibmcloud"
    """
    if not providers:
        providers_list = CLOUD_PROVIDERS.split(",")
    else:
        providers_list = [p.strip() for p in providers.split(",") if p.strip()]

    summary = list_all_cloud_resources(providers_list)
    return JSONResponse(summary)
