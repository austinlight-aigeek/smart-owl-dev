from enum import Enum

from langchain.memory import ConversationBufferMemory


class MemoryTypes(str, Enum):
    CONVERSATION_BUFFER_MEMORY = "ConversationBufferMemory"


MEMORY_CATALOG = {"ConversationBufferMemory": ConversationBufferMemory}
