import aisuite as ai
from .template import LLMClientTemplate

client = ai.Client()

class AnthropicClient(LLMClientTemplate):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def _initialize_client(self):
        self.client = ai.Client({"anthropic": {"api_key": self.api_key}})
        self.model = "anthropic:claude-3-5-sonnet-20240620"

class OpenAIClient(LLMClientTemplate):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def _initialize_client(self):
        self.client = ai.Client({"openai": {"api_key": self.api_key}})
        self.model = "openai:gpt-3.5-turbo"
