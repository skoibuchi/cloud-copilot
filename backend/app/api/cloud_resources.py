from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.tools.multi_cloud_tools import _list_all_cloud_resources
from app.api.deps import get_current_user
from app.core.audit import AuditService

router = APIRouter(prefix="/resources", tags=["cloud"])
audit_service = AuditService()


@router.get("/")
async def cloud_resources(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Return information of all cloud environment
    """
    try:
        summary = _list_all_cloud_resources(user_id=current_user.id)
        audit_service.log(user_id=current_user.id, action="")
        return JSONResponse(summary)
    except Exception as e:
        audit_service.log(user_id=current_user.id, action="app.api.cloud_resources.cloud_resources",
                          success=False, error_message=str(e), log_level="ERROR")
        raise
