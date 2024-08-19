from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import asyncio

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    print("login()")


@router.post("/login", response_class=HTMLResponse)
def login_for_access_token():
    print("login_for_access_token()")

@router.get("/logout", response_class=HTMLResponse)
async def logout():
    await asyncio.sleep(3)
    print("logout()")

    