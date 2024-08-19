from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import asyncio

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def chat_bot():
    print("chat_bot()")

@router.put("/getChatBotResponse")
async def get_bot_response():
    await asyncio.sleep(3)

    print("get_bot_response()")

@router.put("/resetChatModel")
async def reset_chat_model():
    await asyncio.sleep(3)

    print("reset_chat_model()")