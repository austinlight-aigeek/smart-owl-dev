from fastapi import APIRouter

from app.ui.apis import route_chatbot, route_login

api_router_ui = APIRouter()
api_router_ui.include_router(route_chatbot.router, prefix="", tags=["chatbot"])
api_router_ui.include_router(route_login.router, prefix="", tags=["login-ui"])
