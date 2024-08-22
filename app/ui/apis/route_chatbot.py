import traceback

from boto3.resources.base import ServiceResource
from fastapi import APIRouter, Body, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.apis.models.request_model import RequestModel
from app.apis.services.gpt_manager import GPTManagerError
from app.apis.services.llm import DatabricksEndpointLLMError
from app.apis.services.llm_handler import llm_handler
from app.apis.services.public_llms.chain_manager import ChainManagerError
from app.apis.v1.route_login import get_current_user
from app.db.dynamo_db import initialize_db
from app.db.redis_handler import RedisChatRepository, get_redis
from app.db.repository.user import increase_usage
from app.db.session import get_db
from app.ui import templates

router = APIRouter()

availables_public_models = [
    "gpt-3.5-turbo",
    "gpt-4-1106-preview",
    "gpt-4o",
    "Llama-2-70B-Chat",
    "Meta-Llama-3-70b-Instruct",
    "Mixtral-8x7B-Instruct",
    "MPT-7B-Instruct",
    "MPT-30B-Instruct",
    "DBRX-Instruct",
]


@router.get("/", response_class=HTMLResponse)
def chat_bot(request: Request, user_db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")

    if access_token:
        try:
            current_user = get_current_user(access_token, user_db)
            return templates.TemplateResponse(
                "gatekeeper.html",
                {
                    "request": request,
                    "models": current_user.available_models,
                    "username": current_user.email.split("@")[0],
                },
            )
        except HTTPException:
            return templates.TemplateResponse(
                "gatekeeper.html",
                {
                    "request": request,
                    "models": availables_public_models,
                    "landing_page": True,
                    "logout": True,
                },
            )

    return templates.TemplateResponse(
        "gatekeeper.html",
        {"request": request, "models": availables_public_models, "landing_page": True},
    )


@router.put("/getChatBotResponse")
async def get_bot_response(
    request: Request,
    request_data: RequestModel,
    user_db: Session = Depends(get_db),
    log_db: ServiceResource = Depends(initialize_db),
    cache_db: RedisChatRepository = Depends(get_redis),
):
    try:
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                current_user = get_current_user(access_token, user_db)
            except HTTPException:
                return (
                    "Something Wrong while authentication or storing tokens. "
                    "Maybe your token expired, try to log in again"
                )
            except Exception:
                return "Server error, contact administrator."

            if not increase_usage(current_user, user_db):
                return "Reached the quota limit. Request denied."

            chat_id = await cache_db.get_chat_id_from_email(current_user.email)
            if chat_id:
                model = chat_id.split("+")[-1]
                if model != request_data.model:
                    await cache_db.delete_conversation(chat_id)
            try:
                response = await llm_handler(log_db, current_user, request_data, cache_db)
            except GPTManagerError as gpt_error:
                return f"{gpt_error}"
            except DatabricksEndpointLLMError as databricks_llm_error:
                return f"{databricks_llm_error}"
            except ChainManagerError as chain_error:
                return f"{chain_error}"

            return response

        return "You are not logged in"
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()  # This prints the traceback to the standard output
        return "Server error, contact administrator."


@router.put("/resetChatModel")
async def reset_chat_model(
    request: Request,
    model: dict = Body(...),
    user_db: Session = Depends(get_db),
    cache_db: RedisChatRepository = Depends(get_redis),
):
    access_token = request.cookies.get("access_token")
    if access_token:
        current_user = get_current_user(access_token, user_db)
        chat_id = current_user.email + "+" + model["model"]
        if await cache_db.exists(chat_id):
            await cache_db.delete_conversation(chat_id)
