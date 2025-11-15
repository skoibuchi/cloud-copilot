from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.cloud_config import CloudConfigCreate, CloudConfigResponse
from app.schemas.user import UserResponse
from app.database.database import get_db
from app.api.deps import get_current_user
from app.services.cloud_config_service import upsert_cloud_config, list_cloud_configs
from app.core.audit import AuditService

router = APIRouter(prefix="/cloud", tags=["cloud"])
audit_service = AuditService()


@router.post("/save", response_model=CloudConfigResponse)
def save_cloud_config_endpoint(
        cloud_config: CloudConfigCreate,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    try:
        saved = upsert_cloud_config(db=db, user_id=current_user.id, cloud_config=cloud_config)
        audit_service.log(user_id=current_user.id, action="app.api.cloud_config.save_cloud_config_endpoint",
                          resource=f"{cloud_config.provider}/{cloud_config.account_name}")
        return CloudConfigResponse.model_validate({
            "id": saved.id,
            "provider": saved.provider,
            "account_name": saved.account_name,
            "region": saved.region,
            "credentials": saved.credentials
        })
    except Exception as e:
        audit_service.log(user_id=current_user.id, action="app.api.cloud_config.save_cloud_config_endpoint",
                          resource=f"{cloud_config.provider}/{cloud_config.account_name}",
                          success=False, error_message=str(e), log_level="ERROR")
        raise


@router.get("/list")
def list_cloud_configs_endpoint(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    try:
        configs = list_cloud_configs(db=db, user_id=current_user.id)
        audit_service.log(user_id=current_user.id, action="app.api.cloud_config.list_cloud_configs_endpoint",)
        return configs
    except Exception as e:
        audit_service.log(user_id=current_user.id, action="app.api.cloud_config.list_cloud_configs_endpoint",
                          success=False, error_message=str(e), log_level="ERROR")
        raise
