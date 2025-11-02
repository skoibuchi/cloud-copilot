from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.cloud_config import CloudConfigCreate, CloudConfigResponse
from app.schemas.user import UserResponse
from app.database.database import get_db
from app.api.deps import get_current_user
from app.services.cloud_config_service import upsert_cloud_config, list_cloud_configs

router = APIRouter(prefix="/cloud", tags=["cloud"])


@router.post("/save", response_model=CloudConfigResponse)
def save_cloud_config(
        cloud_config: CloudConfigCreate,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    saved = upsert_cloud_config(db=db, user_id=current_user.id, cloud_config=cloud_config)
    return CloudConfigResponse.model_validate({
        "id": saved.id,
        "provider": saved.provider,
        "account_name": saved.account_name,
        "region": saved.region,
        "credentials": saved.credentials
    })


@router.get("/list")
def list_configs(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return list_cloud_configs(db=db, user_id=current_user.id)
