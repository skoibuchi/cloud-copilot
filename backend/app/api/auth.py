from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.database.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.core.audit import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])
audit_service = AuditService()


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        audit_service.log(user_id=None, action="app.api.auth.register", resource=user_in.username,
                          success=False, error_message="Username already exists", log_level="WARN")
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(user_in.password) if user_in.password else None
    user = User(username=user_in.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_service.log(user_id=user.id, action="app.api.auth.register", resource=user_in.username)
    return user


@router.post("/login")
def login(form_data: UserCreate, db: Session = Depends(get_db)):
    """
    Login that sets JWT token in httpOnly cookie
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        audit_service.log(user_id=None, action="app.api.auth.login",
                          success=False, error_message="Invalid credentials", log_level="WARN")
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

    audit_service.log(user_id=user.id, action="app.api.auth.login")
    return response


@router.post("/logout")
def logout(response: Response, current_user=Depends(get_current_user)):
    response.delete_cookie(key="token", path="/")
    audit_service.log(user_id=(current_user.id if current_user else None), action="app.api.auth.logout")
    return {"detail": "Logged out"}
