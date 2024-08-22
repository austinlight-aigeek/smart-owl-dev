from enum import Enum

from langchain_openai import ChatOpenAI

from app.apis.services.llm import ChatLLM


class ProviderTypes(str, Enum):
    OPENAI = "openai"
    DATABRICKS = "databricks"


MODEL_CATALOG = {"openai": ChatOpenAI, "databricks": ChatLLM}
