from langchain.chains import LLMChain
from openai import OpenAIError
from requests.exceptions import RequestException

from app.apis.services.custom_callbacks_handler import get_llm_callback
from app.apis.services.llm import DatabricksEndpointLLMError


class ChainManagerError(OpenAIError):
    """Handle GPTManager exceptions."""

    def __init__(self, message: str):
        self._message = message
        super().__init__(self._message)


class ChainManager:
    """Class used to build a custom langchain Chain."""

    def __init__(self, model, memory, prompt):
        self._base_model = model
        self._base_memory = memory
        self._base_prompt = prompt
        self._init_chain()

    def _init_chain(self):
        self.chain = LLMChain(
            llm=self._base_model, prompt=self._base_prompt, memory=self._base_memory
        )

    async def _predict(self, message: str):
        try:
            with get_llm_callback(llm=self._base_model) as cb:
                response = await self.chain.ainvoke(
                    {self._base_prompt.input_variables[0]: message},
                    include_run_info=True,
                )
                response["usage"] = {
                    "total_tokens": cb.total_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "prompt_tokens": cb.prompt_tokens,
                }
        except OpenAIError as openai_err:
            raise ChainManagerError(openai_err.body["message"])
        except RequestException as err:
            raise DatabricksEndpointLLMError(str(err))

        return response

    async def __call__(self, message: str):
        output = await self._predict(message=message)

        return output
