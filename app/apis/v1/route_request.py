from fastapi import APIRouter

import asyncio

router = APIRouter()

@router.put("/request")
async def forward_gpt_request():

    # Todo
    await asyncio.sleep(3)

    return {"response", {}}




