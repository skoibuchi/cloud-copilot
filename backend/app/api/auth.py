from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.database.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(user_in.password) if user_in.password else None
    user = User(username=user_in.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(form_data: UserCreate, db: Session = Depends(get_db)):
    """
    Login that sets JWT token in httpOnly cookie
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})

    response = JSONResponse(
        content={
            "message": "Logged in",
            "access_token": token,
            "token_type": "bearer"
        }
    )
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=settings.SECURE_CONNECTION,
        samesite="lax",
        max_age=(60 * 60 * 24)
    )
    return response


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="token", path="/")
    return {"detail": "Logged out"}
