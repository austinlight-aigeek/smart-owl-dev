import asyncio
import inspect
from typing import Any, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    ChatMessage,
    ChatMessageRole,
    QueryEndpointResponse,
)
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun
from langchain_core.embeddings import Embeddings
from langchain_core.outputs import Generation, LLMResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import Field
from requests.exceptions import RequestException

from app.core.config import settings


class DatabricksEndpointLLMError(RequestException):
    pass


class ChatLLM(LLM):

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: str = "meta-llama-3-70b-instruct"
    endpoint: Any = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.endpoint = WorkspaceClient(
            host=settings.DATABRICKS_HOST,
            client_id=settings.DATABRICKS_SP_CLIENT_ID,
            client_secret=settings.DATABRICKS_SP_SECRET,
        ).serving_endpoints
        self.model_name = f"databricks-{self.model_name.lower()}"

    @property
    def _llm_type(self) -> str:
        return self.model_name

    def _call_endpoint(self, prompt) -> QueryEndpointResponse:
        # use prompt argument instead of messages argument
        if self.model_name.startswith("databricks-mpt"):
            return self.endpoint.query(
                self.model_name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        messages = [ChatMessage(role=ChatMessageRole.USER, content=prompt)]
        return self.endpoint.query(
            self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    async def acall(self, prompt: str) -> QueryEndpointResponse:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, self._call_endpoint, prompt)
        except RequestException as err:
            raise DatabricksEndpointLLMError(str(err))
        return result

    def _call(
        self,
        prompt: str,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Overrides LLM superclass's `_call` method.
        """
        return self.extract_str_from_response(self._call_endpoint(prompt))

    def extract_str_from_response(self, response: QueryEndpointResponse) -> str:
        if self.model_name.lower().startswith("databricks-mpt"):
            return response.choices[0].text.strip()
        else:
            return response.choices[0].message.content.strip()

    async def _acall(
        self,
        prompt: str,
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Overrides the LLM superclass's `_acall` method.
        Calls the LLM and returns only the string of the response.
        """
        response = await self.acall(prompt)
        return self.extract_str_from_response(response)

    def _generate(
        self,
        prompts: list[str],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []
        llm_output = {}
        llm_output["token_usage"] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        new_arg_supported = inspect.signature(self._call).parameters.get("run_manager")
        new_arg_supported is None, "We are not supporting run_manager"
        for prompt in prompts:
            response = self._call_endpoint(prompt)
            text = self.extract_str_from_response(response)
            usage = response.usage.as_dict()
            llm_output["token_usage"]["completion_tokens"] += usage["completion_tokens"]
            llm_output["token_usage"]["prompt_tokens"] += usage["prompt_tokens"]
            llm_output["token_usage"]["total_tokens"] += usage["total_tokens"]
            generations.append([Generation(text=text)])

        return LLMResult(generations=generations, llm_output=llm_output)

    async def _agenerate(
        self,
        prompts: list[str],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Run the LLM on the given prompt and input."""
        loop = asyncio.get_running_loop()
        llm_result = await loop.run_in_executor(
            None, self._generate, prompts, stop, run_manager, **kwargs
        )

        return llm_result


class EmbeddingLLM(Embeddings):

    def __init__(self, model_name):
        self.endpoint = WorkspaceClient(
            host=settings.DATABRICKS_HOST,
            client_id=settings.DATABRICKS_SP_CLIENT_ID,
            client_secret=settings.DATABRICKS_SP_SECRET,
        ).serving_endpoints
        self.model_name = f"databricks-{model_name.lower()}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed search docs.
        Async function is inherited from Embeddings superclass.
        """

        def batch_texts(texts: list[str], max_chars=10000):
            batch = []
            batch_chars = 0
            for text in texts:
                # If the text is longer than we can fit into a batch, raise an error
                if len(text) > max_chars:
                    raise DatabricksEndpointLLMError(
                        "Too long of an input string to encode an embedding"
                    )

                # If the text fits into the batch, then add it to the batch
                if len(text) + batch_chars <= max_chars:
                    batch.append(text)
                    batch_chars += len(text)
                # If it doesn't fit into the batch, yield the batch, empty it, and add the text
                else:
                    yield batch
                    batch = [text]
                    batch_chars = len(text)
            if len(batch) > 0:
                yield batch

        results = []
        for batch in batch_texts(texts):
            batch_results = self.endpoint.query(self.model_name, input=batch).data
            for res in batch_results:
                results.append(res.embedding)
        assert len(results) == len(texts), "Input texts failed to batch properly"
        return results

    def embed_query(self, text: str) -> list[float]:
        """
        Embed query text. Async function is inherited.
        Async function is inherited from Embeddings superclass.
        """
        results = self.endpoint.query(self.model_name, input=[text]).data
        return results[0].embedding


def load_chat_model(model_name, temperature=0.0, max_tokens=None):
    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        return ChatLLM(
            model_name=model_name, temperature=temperature, max_tokens=max_tokens
        )


def load_embedding_model(model_name):
    if model_name.startswith("text-embedding-"):
        return OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=model_name,
            deployment=model_name,
        )
    else:
        return EmbeddingLLM(model_name=model_name)
