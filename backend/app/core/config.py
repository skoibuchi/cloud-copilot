import os
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings
from typing import ClassVar
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    DB_URL: ClassVar[str] = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    SECRET_KEY: ClassVar[str] = os.getenv("SECRET_KEY", "super-secret-key")
    ENCRYPTION_KEY: ClassVar[str] = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[int] = 60 * 24
    LLM_PROVIDER: ClassVar[str] = os.getenv("LLM_PROVIDER", "gemini")
    CLOUD_PROVIDERS: ClassVar[str] = os.getenv("CLOUD_PROVIDERS", "gcp").lower()
    VECTORSTORE_CLASS: ClassVar[str] = os.getenv("VECTORSTORE_CLASS", "chroma").lower()
    TEMP_UPLOAD_DIR: ClassVar[str] = os.getenv("TEMP_UPLOAD_DIR", "./temp_uploads")
    FRONTEND_URL: ClassVar[str] = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ADMIN_USERNAME: ClassVar[str] = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL: ClassVar[str] = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: ClassVar[str] = os.getenv("ADMIN_PASSWORD", "adminpassword")


settings = Settings()
