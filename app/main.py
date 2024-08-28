import socket
from os import getenv

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.apis.base import api_router
from app.apis.services.gpt_manager import GPTManagerError
from app.apis.services.llm import DatabricksEndpointLLMError
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.ui.apis.base import api_router_ui


def create_tables():
    print("--------------- Engine ------------")
    print(engine)
    print("---------------- Engine End ---------------")
    Base.metadata.create_all(bind=engine)


def include_router(app):
    app.include_router(api_router)


def include_router_ui(app):
    app.include_router(api_router_ui)


def start_application():
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    create_tables()
    include_router(app)
    include_router_ui(app)
    return app


app = start_application()


@app.get("/health")
def home():
    return {"msg": "Welcome to ChatGPT GateKeeper! 🚀🚀🚀"}


@app.exception_handler(GPTManagerError)
def gpt_exception_handler(request: Request, exc: GPTManagerError):
    return JSONResponse(status_code=400, content={"detail": exc.body["message"]})


@app.exception_handler(DatabricksEndpointLLMError)
def fmm_exception_handler(request: Request, exc: DatabricksEndpointLLMError):
    return JSONResponse(status_code=400, content={"detail": exc.user_message})


if getenv("RUN_LOCALLY"):

    @app.middleware("http")
    async def add_middleware(request: Request, call_next):
        response = await call_next(request)
        print(f"Container ID: {socket.gethostname()}")
        return response


if getenv("DEBUG_LANGCHAIN"):
    from langchain.globals import set_debug

    set_debug(True)
