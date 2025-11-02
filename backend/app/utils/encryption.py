from cryptography.fernet import Fernet
from app.core.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY.encode())


if not settings.ENCRYPTION_KEY:
    key = Fernet.generate_key()
    print("ENCRYPTION_KEY not found. Generated temporary key.")
    settings.ENCRYPTION_KEY = key.decode()


def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
