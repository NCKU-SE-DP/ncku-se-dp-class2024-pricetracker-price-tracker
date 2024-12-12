from abc import ABC, abstractmethod
from .exception import DomainMismatchException
from pydantic import BaseModel, Field

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

    def validate_key(self):
        
        if not self.api_key:
            raise ValueError("API key is not provided.")

    @abstractmethod
    def extract_keywords(self, content: str, prompt: MessageInterface) -> dict:
        """
        Abstract method for extracting keywords from the given content.
        Concrete implementations need to be provided in subclasses.
        :param content: The content to extract keywords from.
        :param prompt: The prompt to use for keyword extraction.
        :return: The extracted keywords.
        """
        return NotImplemented

    @abstractmethod
    def generate_summary(self, content: str, prompt: MessageInterface) -> dict:
        """
        Abstract method for generating a summary.
        Concrete implementations need to be provided in subclasses.
        :param content: The content to generate a summary for.
        :param prompt: The prompt to use for generating the summary.
        :return: The generated summary.
        """
        return NotImplemented