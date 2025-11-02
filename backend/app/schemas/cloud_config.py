from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class CloudConfigBase(BaseModel):
    provider: str
    account_name: str
    region: Optional[str] = None


class CloudConfigCreate(CloudConfigBase):
    credentials: Optional[Dict[str, Any]] = None


class CloudConfigResponse(CloudConfigBase):
    id: int
    credentials: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
