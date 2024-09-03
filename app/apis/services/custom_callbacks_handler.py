import threading
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator, Optional

from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.outputs import LLMResult
from langchain_core.tracers.context import register_configure_hook

from app.apis.services.public_llms.models import MODEL_CATALOG


class DatabricksCallbackHandler(BaseCallbackHandler):
    """Callback Handler that tracks DataBricks info."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.total_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"Successful Requests: {self.successful_requests}\n"
        )

    @property
    def always_verbose(self) -> bool:
        """Whether to call verbose callbacks even if verbose is False."""
        return True

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        """Print out the prompts."""
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Print out the token."""
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Collect token usage."""
        if response.llm_output is None:
            return None

        if "token_usage" not in response.llm_output:
            with self._lock:
                self.successful_requests += 1
            return None

        # compute tokens for this request
        token_usage = response.llm_output["token_usage"]
        completion_tokens = token_usage.get("completion_tokens", 0)
        prompt_tokens = token_usage.get("prompt_tokens", 0)

        # update shared state behind lock
        with self._lock:
            self.total_tokens += token_usage.get("total_tokens", 0)
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.successful_requests += 1

    def __copy__(self) -> "DatabricksCallbackHandler":
        """Return a copy of the callback handler."""
        return self

    def __deepcopy__(self, memo: Any) -> "DatabricksCallbackHandler":
        """Return a deep copy of the callback handler."""
        return self


databricks_callback_var: ContextVar[Optional[DatabricksCallbackHandler]] = ContextVar(
    "databrciks_callback", default=None
)
openai_callback_var: ContextVar[Optional[OpenAICallbackHandler]] = ContextVar(
    "openai_callback", default=None
)

register_configure_hook(databricks_callback_var, True)
register_configure_hook(openai_callback_var, True)


@contextmanager
def get_llm_callback(
    llm: BaseLanguageModel,
) -> Generator[DatabricksCallbackHandler | OpenAICallbackHandler, None, None]:
    """Get the MODEL_CATALOG callback handler in a context manager.
    which conveniently exposes token and cost information.

    Returns:
        DatabricksCallbackHandler | OpenAICallbackHandler: The callback handler.

    Example:
        >>> with get_llm_callback() as cb:
        ...     # Use the callback handler
    """
    if isinstance(llm, MODEL_CATALOG["openai"]):
        cb = OpenAICallbackHandler()
        openai_callback_var.set(cb)
        yield cb
        openai_callback_var.set(None)
    elif isinstance(llm, MODEL_CATALOG["databricks"]):
        cb = DatabricksCallbackHandler()
        databricks_callback_var.set(cb)
        yield cb
        databricks_callback_var.set(None)
