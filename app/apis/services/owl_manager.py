import json
from abc import abstractmethod
from typing import Optional
from urllib.parse import unquote

from databricks.vector_search.client import VectorSearchClient, VectorSearchIndex
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.schema import messages_from_dict
from langchain_community.vectorstores import DatabricksVectorSearch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages.base import BaseMessage
from langchain_core.prompts import PromptTemplate

from app.apis.services.llm import load_chat_model, load_embedding_model
from app.core.config import settings


class InvalidDataFormatException(Exception):
    pass


class CustomVectorSearch(DatabricksVectorSearch):
    """
    Adds formatted metadata explicitly to Document texts for DatabricksVectorSearch
    """

    def __init__(
        self,
        index: VectorSearchIndex,
        data_format: str,
        embedding: Optional[Embeddings] = None,
        text_column: Optional[str] = None,
        columns: Optional[list[str]] = None,
    ):
        self.data_format = data_format
        super().__init__(
            index, embedding=embedding, text_column=text_column, columns=columns
        )

    def _add_metadata_to_text(self, text_content, metadata):
        if self.data_format == "pdf":
            title = unquote(metadata["filename"][:-4])
            source_string = f"<TITLE>{title}</TITLE>\n<PAGE_NUMBER>{int(metadata['page_number'])}</PAGE_NUMBER>"  # noqa: E501. f-string metadata for prompt
        elif self.data_format == "academy":
            source_string = metadata["breadcrumbs"]
        else:
            raise InvalidDataFormatException(
                "Invalid data format for Document formatting"
            )

        return f"<QUOTE>\n<TEXT>\n. . . {text_content} . . .\n</TEXT>\n<SOURCE>\n{source_string}\n</SOURCE>\n</QUOTE>"  # noqa: E501. f-string metadata for prompt

    def _parse_search_response(
        self, search_resp: dict, ignore_cols: Optional[list[str]] = None
    ) -> list[tuple[Document, float]]:
        """Parse the search response into a list of Documents with score."""
        if ignore_cols is None:
            ignore_cols = []

        columns = [
            col["name"]
            for col in search_resp.get("manifest", dict()).get("columns", [])
        ]
        docs_with_score = []
        for result in search_resp.get("result", dict()).get("data_array", []):
            doc_id = result[columns.index(self.primary_key)]
            text_content = result[columns.index(self.text_column)]
            metadata = {
                col: value
                for col, value in zip(columns[:-1], result[:-1])
                if col not in ([self.primary_key, self.text_column] + ignore_cols)
            }
            metadata[self.primary_key] = doc_id
            score = result[-1]
            doc = Document(
                page_content=self._add_metadata_to_text(text_content, metadata),
                metadata=metadata,
            )
            docs_with_score.append((doc, score))
        return docs_with_score


class OwlChatbot:
    """
    General parent class for handling common chatbot logic
    """

    def __init__(
        self,
        chatbot_name: str,
        retrieved_columns: list[str],
        data_format: str,
        config: dict,
        chat_message_history: Optional[str] = None,
    ):
        self.chatbot_name = chatbot_name
        self.config = config
        self.retrieved_columns = retrieved_columns
        self.data_format = data_format
        self.host = settings.DATABRICKS_HOST
        self.__chat_memory = None

        self.vector_search_endpoint_name = settings.VECTOR_SEARCH_ENDPOINT
        self.vector_index_name = settings.get_vector_index_fullname(self.chatbot_name)

        if chat_message_history:
            retrieve_from_cache = json.loads(chat_message_history)
            retrieved_messages = messages_from_dict(retrieve_from_cache)
            self.__chat_memory = ChatMessageHistory(messages=retrieved_messages)

        # models
        self.embedding_model = load_embedding_model(
            self.config["embedding"]["model_name"]
        )
        self.llm = load_chat_model(
            self.config["llm"]["model_name"],
            temperature=self.config["llm"]["temperature"],
            max_tokens=self.config["llm"]["max_tokens"],
        )

        # prompts
        self.condense_question_prompt = PromptTemplate.from_template(
            self.config["condense_question_prompt"]
        )
        self.instruction_prompt = PromptTemplate.from_template(
            self.config["instruction_prompt"]
        )

        self.retriever = self._load_retriever()
        self.rag_chain = self._load_rag_chain()

    def get_message_chat_history(self) -> list[BaseMessage]:
        return self.rag_chain.memory.chat_memory.messages

    def _load_retriever(self):
        client_id = settings.DATABRICKS_SP_CLIENT_ID
        secret = settings.DATABRICKS_SP_SECRET
        vsc = VectorSearchClient(
            workspace_url=self.host,
            service_principal_client_id=client_id,
            service_principal_client_secret=secret,
        )
        vs_index = vsc.get_index(
            endpoint_name=self.vector_search_endpoint_name,
            index_name=self.vector_index_name,
        )
        vectorstore = CustomVectorSearch(
            vs_index,
            self.data_format,
            text_column="chunk",
            embedding=self.embedding_model,
            columns=self.retrieved_columns,
        )
        retriever = vectorstore.as_retriever()
        return retriever

    def _load_rag_chain(self):
        chain_type_kwargs = {"prompt": self.instruction_prompt}
        if self.__chat_memory:
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                input_key="question",
                output_key="answer",
                return_messages=True,
                chat_memory=self.__chat_memory,
            )
        else:
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                input_key="question",
                output_key="answer",
                return_messages=True,
            )

        rag_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            chain_type="stuff",
            memory=memory,
            retriever=self.retriever,
            return_source_documents=False,
            combine_docs_chain_kwargs=chain_type_kwargs,
            condense_question_prompt=self.condense_question_prompt,
        )
        return rag_chain

    @abstractmethod
    async def execute(self, query, output_dict=False):
        pass

    async def __call__(self, query, output_dict=False):
        return await self.execute(query, output_dict)


class OwlChatbotPDF(OwlChatbot):
    """
    Child class for chatbots which use PDFs for RAG
    """

    def __init__(self, chatbot_name: str, chat_message_history: Optional[str] = None):
        self.config = settings.CHATBOT_CONFIG["pdf"][chatbot_name]
        self.job_title = self.config["job_title"]
        self.topic = self.config["topic"]
        self.filenames = self.config["filenames"]
        self.titles = [unquote(fname[:-4]) for fname in self.filenames]
        self.docs_info_prompt = "".join(
            [f"\tTitle: {title}\n" for title in self.titles]
        )[:-1]

        super().__init__(
            chatbot_name,
            ["id", "filename", "page_number"],
            "pdf",
            self.config,
            chat_message_history=chat_message_history,
        )

    async def execute(self, query, output_dict=False):
        result = await self.rag_chain.ainvoke(
            {
                "question": query,
                "job_title": self.job_title,
                "topic": self.topic,
                "document_names": self.docs_info_prompt,
            }
        )
        if output_dict:
            return result
        return result["answer"]


class OwlChatbotAcademy(OwlChatbot):
    """
    Child class for chatbots which use Academy dumps for RAG
    """

    def __init__(self, chatbot_name: str, chat_message_history: Optional[str] = None):
        self.config = settings.CHATBOT_CONFIG["academy"][chatbot_name]
        self.course = self.config["course"]
        self.course_parsed = self.course.replace("-", " ").title()
        super().__init__(
            chatbot_name,
            ["id", "course", "breadcrumbs"],
            "academy",
            self.config,
            chat_message_history,
        )

    async def execute(self, query, output_dict=False):
        result = await self.rag_chain.ainvoke(
            {"question": query, "course": self.course_parsed}
        )
        if output_dict:
            return result
        return result["answer"]
