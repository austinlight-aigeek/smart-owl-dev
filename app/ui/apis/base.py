from fastapi import APIRouter
from app.ui.apis import route_chatbot, route_login

ui_router = APIRouter()
ui_router.include_router(route_chatbot.router, prefix="", tags=["chatbot"])
ui_router.include_router(route_login.router, prefix="", tags=["login-ui"])