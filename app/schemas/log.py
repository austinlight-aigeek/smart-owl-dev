from typing import Optional
from pydantic import BaseModel, root_validator


class CreateLog(BaseModel):
    user_id: str
    user_email: str
    project_name: str
    openai_key_type: str
    is_success: bool
    gpt_request: dict
    gpt_response: dict

    # placeholder for future logic
    @root_validator(pre=True)
    def generate_slug(cls, values):
        return values


class ShowLog(BaseModel):
    id: str
    user_id: str
    user_email: str
    project_name: str
    openai_key_type: str
    is_success: bool
    gpt_request: dict
    gpt_response: dict
    created_at: str

    class Config:
        orm_mode = True

    
class MessageResponse(BaseModel):
    content: str
    role: str


class ChoiceResponse(BaseModel):
    index: int
    finish_reason: str
    message: MessageResponse
    logprobs: Optional[float]