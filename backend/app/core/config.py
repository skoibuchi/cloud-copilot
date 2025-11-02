import os
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings
from typing import ClassVar
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    # DB
    DB_URL: ClassVar[str] = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    # SECURE KEY for JWT
    SECRET_KEY: ClassVar[str] = os.getenv("SECRET_KEY", "super-secret-key")
    # ENCRYPTION KEY for user information
    ENCRYPTION_KEY: ClassVar[str] = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    # ACCESS TOKEN EXPIRE(MINUTES)
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[int] = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
    # LLM PROVIDER
    LLM_PROVIDER: ClassVar[str] = os.getenv("LLM_PROVIDER", "gemini")
    # GEMINI
    GEMINI_API_KEY = os.getenv("LLM_GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("LLM_GEMINI_MODEL")
    # OpenAI
    OPENAI_API_KEY = os.getenv("LLM_OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("LLM_OPENAI_MODEL")
    # watsonx
    WATSONX_API_KEY = os.getenv("LLM_WATSONX_API_KEY")
    WATSONX_PROJECT_ID = os.getenv("LLM_WATSONX_PROJECT_ID")
    WATSONX_URL = os.getenv("LLM_WATSONX_URL")
    WATSONX_MODEL = os.getenv("LLM_WATSONX_MODEL")
    # vectorstore
    VECTORSTORE_CLASS: ClassVar[str] = os.getenv("VECTORSTORE_CLASS", "chroma").lower()
    # temp folder for uploaded files
    TEMP_UPLOAD_DIR: ClassVar[str] = os.getenv("TEMP_UPLOAD_DIR", "./temp_uploads")
    # frontend
    FRONTEND_URL: ClassVar[str] = os.getenv("FRONTEND_URL", "http://localhost:3000")
    SECURE_CONNECTION: ClassVar[str] = os.getenv("SECURE_CONNECTION", "True").lower() == 'true'
    # Admin user
    ADMIN_USERNAME: ClassVar[str] = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: ClassVar[str] = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: ClassVar[str] = os.getenv("ADMIN_PASSWORD", "adminpassword")


settings = Settings()
