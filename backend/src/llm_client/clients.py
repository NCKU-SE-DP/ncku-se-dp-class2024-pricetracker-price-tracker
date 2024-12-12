import aisuite
from .template import LLMClientTemplate

class OpenAIClient(LLMClientTemplate):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def _initialize_client(self):
        self.client = aisuite.Client({"openai": {"api_key": self.api_key}})
        self.model = "openai:gpt-4o-mini"

class AnthropicClient(LLMClientTemplate):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    def _initialize_client(self):
        self.client = aisuite.Client({"anthropic": {"api_key": self.api_key}})
        self.model = "anthropic:claude-3-5-sonnet-20240620"