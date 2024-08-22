from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.apis.models.request_model import AvailableModels
from app.apis.v1.route_login import authenticate_user, get_current_user
from app.core.security import create_access_token
from app.db.redis_handler import RedisChatRepository, get_redis
from app.db.repository.user import reset_usage
from app.db.session import get_db
from app.ui import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    access_token = request.cookies.get("access_token")
    if access_token:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            error = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {"request": request, "error": error})
        access_token = create_access_token(data={"sub": user.email})

        reset_usage(user, db)
        models = user.available_models

        response = templates.TemplateResponse(
            "gatekeeper.html",
            {"request": request, "models": models, "username": user.email.split("@")[0]},
        )
        response.set_cookie(key="access_token", value=f"{access_token}", httponly=True)

        return response
    except Exception:
        error = "Something Wrong while authentication or storing tokens!"
        return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.get("/logout", response_class=HTMLResponse)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    cache_db: RedisChatRepository = Depends(get_redis),
):
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            current_user = get_current_user(access_token, db)
        except HTTPException:
            current_user = None  # It means that access_token´s expired
        if current_user:
            for model in AvailableModels.__members__.values():
                chat_id = current_user.email + "+" + model
                if await cache_db.exists(chat_id):
                    await cache_db.delete_conversation(chat_id)
    msg = "Logout successfully"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie("access_token")
    return response
