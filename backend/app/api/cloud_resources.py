from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.tools.multi_cloud_tools import _list_all_cloud_resources
from app.api.deps import get_current_user

router = APIRouter(prefix="/resources", tags=["cloud"])


@router.get("/")
async def cloud_resources(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Return information of all cloud environment
    """
    user_id = current_user.id
    summary = _list_all_cloud_resources(user_id=user_id)
    return JSONResponse(summary)
