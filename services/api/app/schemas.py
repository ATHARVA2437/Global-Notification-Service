from pydantic import BaseModel
from typing import Optional, Dict

class SendRequest(BaseModel):
    channel: str
    recipient: str
    template_id: Optional[str] = None
    payload: Optional[Dict] = {}
    idempotency_key: Optional[str] = None

class SendResponse(BaseModel):
    id: str
    status: str
