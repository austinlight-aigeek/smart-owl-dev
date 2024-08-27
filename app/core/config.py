import os

import yaml
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Smart Owl"
    PROJECT_VERSION: str = "0.0.6"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv(
        "POSTGRES_SERVER",
        "localhost",
    )
    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT",
        5432,
    )
    POSTGRES_DB: str = os.getenv(
        "POSTGRES_DB",
        "tdd",
    )
    DATABASE_URL = URL.create(
        "postgresql",
        POSTGRES_USER,
        POSTGRES_PASSWORD,
        POSTGRES_SERVER,
        int(POSTGRES_PORT),
        POSTGRES_DB,
    )

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "fake_secret",
    )
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # in mins

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION")
    DYNAMO_DB_TABLE: str = os.getenv("DYNAMO_DB_TABLE")

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION")
    DYNAMO_DB_TABLE: str = os.getenv("DYNAMO_DB_TABLE")

    DATABRICKS_HOST: str = os.getenv("DATABRICKS_HOST")
    DATABRICKS_SP_CLIENT_ID: str = os.getenv("DATABRICKS_SP_CLIENT_ID")
    DATABRICKS_SP_SECRET: str = os.getenv("DATABRICKS_SP_SECRET")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    CATALOG: str = "applied_machine_learning"
    SCHEMA: str = f"chatbot_{ENVIRONMENT}"
    DATABRICKS_PATH: str = f"{CATALOG}.{SCHEMA}"
    VECTOR_SEARCH_ENDPOINT: str = f"chatbot_vector_search_{ENVIRONMENT}"

    OPENAI_API_KEY: str = os.getenv("OPEN_AI_KEY")

    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT"))

    if os.getenv("RUN_LOCALLY"):
        DYNAMO_DB_ENDPOINT: str = os.getenv("DYNAMO_DB_ENDPOINT")

    with open("app/core/config.yaml", "r", encoding="utf-8") as f:
        CHATBOT_CONFIG: dict = yaml.safe_load(f)["smart_owl"]["chatbots"]

    @staticmethod
    def get_chunk_table_name(chatbot_name: str):
        return f"chunks_{chatbot_name}".lower()

    @staticmethod
    def get_chunk_table_fullname(chatbot_name: str):
        table_name = Settings.get_chunk_table_name(chatbot_name)
        return f"{Settings.DATABRICKS_PATH}.{table_name}"

    @staticmethod
    def get_vector_index_name(chatbot_name: str):
        table_name = Settings.get_chunk_table_name(chatbot_name)
        return f"{table_name}_vs_index"

    @staticmethod
    def get_vector_index_fullname(chatbot_name: str):
        index_name = Settings.get_vector_index_name(chatbot_name)
        return f"{Settings.DATABRICKS_PATH}.{index_name}"


settings = Settings()
