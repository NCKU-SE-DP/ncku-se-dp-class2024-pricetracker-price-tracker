from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import aisuite as ai
client = ai.Client()

models = ["openai:gpt-3.5-turbo", "anthropic:claude-3-5-sonnet-20240620"]


class MessagePassingInterfaceExample(BaseModel):
    key: str = Field(
        default=...,
        example="example",
        description="description"
    )

class MessageInterface(BaseModel):
    system_content: str = Field(...)
    user_content: str = Field(...)
    
    @property
    def generate_prompt(self):
        return [{"role": "system", "content": f"{self.system_content}"},
                {"role": "user", "content": f"{self.user_content}"}]

class LLMClient(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def generate_text(self, prompt: MessageInterface) -> dict:
        """
        Abstract method for generating text content.
        Concrete implementations need to be provided in subclasses.
        :param prompt: The prompt message.
        :param kwargs: Additional optional parameters (e.g., temperature, max tokens).
        :return: The response content (dictionary format).
        """
        return NotImplemented