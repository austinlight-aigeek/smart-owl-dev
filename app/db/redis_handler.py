from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings


class RedisChatRepository:

    def __init__(self, host: str, port: int):
        self.__time_to_expire_s: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        self.__redis_client = Redis(host=host, port=port, decode_responses=True)

    async def save_conversation(self, chat_id: str, messages: str):
        await self.__redis_client.set(chat_id, messages, ex=self.__time_to_expire_s)

    async def get_conversation(self, chat_id: str) -> str:
        messages = await self.__redis_client.get(chat_id)
        return messages

    async def delete_conversation(self, chat_id: str):
        await self.__redis_client.delete(chat_id)

    async def get_chat_id_from_email(self, email: str) -> Optional[str]:
        chat_id = await self.__redis_client.keys(f"{email}*")
        return chat_id[0] if chat_id else None

    async def exists(self, key: str) -> int:
        return await self.__redis_client.exists(key)


def get_redis() -> RedisChatRepository:
    return RedisChatRepository(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
