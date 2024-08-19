import socket
from os import getenv

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.apis.base import api_router
from app.ui.apis.base import ui_router




def start_application():
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    app.include_router(api_router)
    app.include_router(ui_router)

    return app

app = start_application()

if getenv("RUN_LOCALLY"):

    @app.middleware("http")
    async def add_middleware(request: Request, call_next):
        response = await call_next(request)
        print(f"Container ID: {socket.gethostname()}")

        return response

if getenv("DEBUG_LANGCHAIN"):
    from langchain.globals import set_debug

    set_debug(True)