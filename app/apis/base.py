from fastapi import APIRouter

from app.apis.v1 import route_log, route_login, route_request, route_user

api_router = APIRouter()
api_router.include_router(route_user.router, prefix="", tags=["users"])
api_router.include_router(route_log.router, prefix="", tags=["logs"])
api_router.include_router(route_login.router, prefix="", tags=["login"])
api_router.include_router(route_request.router, prefix="", tags=["request"])
