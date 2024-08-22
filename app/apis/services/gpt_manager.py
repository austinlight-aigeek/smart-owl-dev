from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings


class GPTManagerError(OpenAIError):
    """Handle GPTManager exceptions."""

    def __init__(self, message: str):
        self._message = message
        super().__init__(self._message)


class GPTManager:
    def __init__(self, **kwargs):
        """
        Initialize the OpenAI API client with the provided API key.
        """
        # openai.organization = "org-..."
        load_dotenv()
        # TODO: Check if valid model
        self.model = kwargs.get("model", "gpt-3.5-turbo")
        self.temperature = kwargs.get("temperature", 0)
        self.top_p = kwargs.get("top_p", 1)
        self.frequency_penalty = kwargs.get("frequency_penalty", 0)
        self.presence_penalty = kwargs.get("presence_penalty", 0)
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _handle_response(self, response):
        """
        Handle the API response, e.g., error handling, logging, or parsing the response.
        """
        try:
            # return self.model
            return response
        except ValueError:
            print("Unexpected API response format.")

    async def complete(self, prompt):
        """
        Call the OpenAI API to get completions based on the provided prompt.
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
        except OpenAIError as openai_err:
            raise GPTManagerError(openai_err.body["message"])

        return self._handle_response(response)
