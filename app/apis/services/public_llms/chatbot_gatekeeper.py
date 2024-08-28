import json
import time
import warnings
from typing import Optional

from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import messages_from_dict
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages.base import BaseMessage

from app.apis.services.public_llms.chain_manager import ChainManager
from app.apis.services.public_llms.config import (
    available_memories,
    available_models,
    config_memories,
    config_models,
    config_prompts,
    default_memory_type,
    default_model_type,
    default_prompt_template_type,
)
from app.apis.services.public_llms.memory import MEMORY_CATALOG
from app.apis.services.public_llms.models import MODEL_CATALOG
from app.core.config import settings
from app.schemas.log import CreateChainResponse


class ChatBotGateKeeper:
    """Class used to build a custom langchain Chatbot."""

    def __init__(
        self,
        model_type: str = "gpt-3.5-turbo",
        memory_type: str = "ConversationBufferMemory",
        prompt_template_type: str = "default",
        chat_message_history: Optional[str] = None,
    ):
        self.__openai_api_key = settings.OPENAI_API_KEY
        self._model_type = model_type
        chat_memory = None
        if chat_message_history:
            retrieve_from_cache = json.loads(chat_message_history)
            retrieved_messages = messages_from_dict(retrieve_from_cache)
            chat_memory = ChatMessageHistory(messages=retrieved_messages)
        (
            self._model,
            self._memory,
            self._prompt,
        ) = self.__init_bot_config(
            self._model_type, memory_type, prompt_template_type, chat_memory
        )
        self._chain = ChainManager(
            model=self._model,
            memory=self._memory,
            prompt=self._prompt,
        )

    def get_message_chat_history(self) -> list[BaseMessage]:
        return self._memory.chat_memory.messages

    def __init_bot_config(
        self,
        model_type: str,
        memory_type: str,
        prompt_template_type: str,
        chat_memory: InMemoryChatMessageHistory,
    ):
        """Initialize model, memory and prompt template configurations."""
        for provider, models in available_models.items():
            for model in models:
                if model_type == model:
                    model_config = {
                        "provider": provider,
                        "model": model,
                        "parameters": config_models["providers"][provider][
                            "parameters"
                        ],
                    }
        if "model_config" not in locals():
            warnings.warn(
                f"Got unknown model type: {model_type}. "
                f"Valid types are: {MODEL_CATALOG.keys()}. Setting default model: gpt-3.5-turbo"
            )
            model_config = default_model_type
        provider = model_config.get("provider")
        model = MODEL_CATALOG[provider](
            model_name=model_config["model"],
            openai_api_key=self.__openai_api_key,
            **model_config["parameters"],
        )

        if memory_type in available_memories:
            memory_config = {
                "memory_type": memory_type,
                "parameters": config_memories["type_memories"][memory_type][
                    "parameters"
                ],
            }
        else:
            warnings.warn(
                f"Got unknown memory type: {memory_type}. "
                f"Valid types are: {MEMORY_CATALOG.keys()}. Setting default memory: ConversationBufferMemory"  # noqa: E501 Warning messages
            )
            memory_config = default_memory_type
        if chat_memory:
            memory = MEMORY_CATALOG[memory_type](
                **memory_config["parameters"], chat_memory=chat_memory
            )
        else:
            memory = MEMORY_CATALOG[memory_type](**memory_config["parameters"])

        prompt_template_config = config_prompts["prompt_templates"].get(
            prompt_template_type, default_prompt_template_type
        )
        human_message = prompt_template_config["human_message_prompt_template"][
            "content"
        ]
        human_message_variable = prompt_template_config[
            "human_message_prompt_template"
        ]["variable_name"]
        prompt = ChatPromptTemplate(
            input_variables=[human_message_variable, memory.memory_key],
            messages=[
                MessagesPlaceholder(variable_name=memory.memory_key),
                HumanMessagePromptTemplate.from_template(human_message),
            ],
        )

        return model, memory, prompt

    def __parse_response(self, chain_response: dict):
        """Parse Chain Response to feed it into lOG db."""
        current_content = chain_response["content"]
        choices = []
        for message in chain_response["messages"]:
            message_type, content = message.type, message.content
            if content == current_content:
                continue
            choices.append(
                {
                    "index": len(choices),
                    "finish_reason": "stop",
                    "message": {"content": content, "role": message_type},
                    "logprobs": None,
                }
            )

        return CreateChainResponse(
            created=int(time.time()),
            usage=chain_response["usage"],
            model=self._model_type,
            id=str(chain_response["__run"].run_id),
            choices=choices,
            system_fingerprint=None,
            object="chat.completion",
        )

    async def _predict(self, message: str, output_dict: bool = True):
        response = await self._chain(message)
        parsed_response = self.__parse_response(response)
        if output_dict:
            return parsed_response

        return parsed_response.choices[-1].message.content

    async def __call__(self, message: str, output_dict: bool = True):
        output = await self._predict(message=message, output_dict=output_dict)

        return output
