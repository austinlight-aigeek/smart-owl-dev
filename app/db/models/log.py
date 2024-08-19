from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel


class Log(BaseModel):
    id: str
    user_id: str
    user_email: str
    project_name: str
    openai_key_type: str
    is_success: bool
    gpt_request: dict
    gpt_response: dict
    created_at: str

    def __init__(self, **data):
        super().__init__(id=str(uuid4()), created_at=datetime.utcnow().isoformat(), **data)