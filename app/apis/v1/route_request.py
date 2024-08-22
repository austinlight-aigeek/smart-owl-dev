from boto3.resources.base import ServiceResource
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.models.request_model import RequestModel
from app.apis.services.gpt_manager import GPTManagerError
from app.apis.services.llm import DatabricksEndpointLLMError
from app.apis.services.llm_handler import llm_handler
from app.apis.v1.route_login import get_current_user
from app.db.dynamo_db import initialize_db
from app.db.models.user import User
from app.db.repository.user import increase_usage
from app.db.session import get_db

router = APIRouter()


@router.put("/request")
async def forward_gpt_request(
    request_data: RequestModel,
    user_db: Session = Depends(get_db),
    log_db: ServiceResource = Depends(initialize_db),
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="🚧 Service not available for now. Please use the UI instead. 😊",
    )
    if not increase_usage(current_user, user_db):
        return {"response": "Reached the quota limit. Request denied."}

    try:
        response = await llm_handler(log_db, current_user, request_data)
    except GPTManagerError as gpt_error:
        return f"{gpt_error}"
    except DatabricksEndpointLLMError as llm_error:
        return f"{llm_error}"

    return {"response": response}
