from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_user(db: Session, user: UserCreate, is_admin: bool = False):
    username = user.username
    hashed_password = hash_password(user.password)
    email = user.email
    user = User(username=username, hashed_password=hashed_password, email=email, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def upsert_user(db: Session, user: UserCreate, is_admin: bool):
    existing_user = db.query(User).filter(User.username == user.username).first()
    username = user.username
    hashed_password = hash_password(user.password)
    email = user.email

    if not existing_user:
        db_user = User(username=username, hashed_password=hashed_password, email=email, is_admin=is_admin)
        db.add(db_user)
    else:
        existing_user.username = user.username
        existing_user.email = user.email
        existing_user.hashed_password = hashed_password
        existing_user.is_admin = is_admin
        db_user = existing_user

    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
