from app.services.user_service import upsert_user
from app.schemas.user import UserCreate
from app.database.database import SessionLocal
from app.core.config import settings


def create_admin_user():
    db = SessionLocal()
    username = settings.ADMIN_USERNAME
    password = settings.ADMIN_PASSWORD
    email = settings.ADMIN_EMAIL
    admin_user = UserCreate(username=username, password=password, email=email)
    saved_user = upsert_user(db=db, user=admin_user, is_admin=True)
    db.close()
    return saved_user
