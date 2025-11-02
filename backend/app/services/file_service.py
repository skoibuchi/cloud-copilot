import os
from typing import List
from fastapi import UploadFile
from app.tools.rag_tools import RAGToolClass


class FileService:
    def __init__(self):
        pass

    async def save_files(self, files: List[UploadFile]):
        paths = []
        for f in files:
            save_path = f"./temp_uploads/{f.filename}"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as buffer:
                buffer.write(await f.read())
            paths.append(save_path)
        return paths

    def add_to_vectorstore(self, file_paths: List[str], rag_tool: RAGToolClass):
        return rag_tool.add_document(file_paths=file_paths)
