import abc
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
class MessageInterface(BaseModel):
    """
    message for LLM
    """
    system_content: str = Field(...)
    user_content: str = Field(...)

    @property
    def to_dict(self):
        value = [
            {"role": "system", "content": f"{self.system_content}"},
            {"role": "user", "content": f"{self.user_content}"},
        ]
        return value
    

class LLMClientBase(metaclass=abc.ABCMeta):
    """
    Abstract defining the structure for an LLM client.
    """
    openai_client: OpenAI | None  

    @abc.abstractmethod
    def _generate(self, messages: MessageInterface) -> str:
        """
        response based on the prompt.
        :param messages: MessageInterface
        :return: The generated text response from the LLM API.
        """
        pass