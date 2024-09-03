from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator

from app.apis.models.request_model import AvailableModels


# properties required during user creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    project_name: str = Field(...)
    team_name: str = Field(...)
    contact_email: EmailStr
    account_type: str = Field(...)
    openai_key_type: str = Field(...)
    openai_key_name: str = Field(...)
    quota: int = Field(...)
    is_super_user: bool = Field(...)
    available_models: list[str] = Field(...)

    @validator("available_models")
    def validate_available_models(cls, models):
        for model in models:
            if model not in AvailableModels.__members__.values():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{model} is not a valid model",
                )
        return models


class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=4)
    is_active: Optional[bool] = Field(None)
    project_name: Optional[str] = Field(None)
    team_name: Optional[str] = Field(None)
    contact_email: Optional[EmailStr]
    account_type: Optional[str] = Field(None)
    openai_key_type: Optional[str] = Field(None)
    openai_key_name: Optional[str] = Field(None)
    quota: Optional[int] = Field(None)
    is_superuser: Optional[bool] = Field(None)
    available_models: Optional[list[str]] = Field(None)

    @validator("available_models")
    def validate_available_models(cls, models):
        for model in models:
            if model not in AvailableModels.__members__.values():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{model} is not a valid model",
                )
        return models

    class Config:
        schema_extra = {
            "example": {
                "password": "string",
                "is_active": True,
                "project_name": "string",
                "team_name": "string",
                "contact_email": "user@example.com",
                "account_type": "string",
                "openai_key_type": "string",
                "openai_key_name": "string",
                "quota": 0,
                "is_superuser": True,
                "available_models": [model.value for model in AvailableModels],
            }
        }


class ShowUser(BaseModel):
    id: int
    email: EmailStr
    project_name: str
    team_name: str
    team_name: str
    contact_email: EmailStr
    account_type: str
    openai_key_type: str
    openai_key_name: str
    quota: int
    usage: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    available_models: list[str] = [model.value for model in AvailableModels]

    class Config:  # tells pydantic to convert even non dict obj to json
        orm_mode = True
