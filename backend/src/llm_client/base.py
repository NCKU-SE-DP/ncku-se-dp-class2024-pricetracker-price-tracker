import abc
from pydantic import BaseModel, Field
from openai import OpenAI

class MessagePassingInterface(BaseModel):
    system_content: str = Field(...)
    user_content: str = Field(...)
    
    @property
    def to_dict(self) -> list[dict[str, str]]:
        dicts = [
            {"role": "system", "content": f"{self.system_content}"},
            {"role": "user", "content": f"{self.user_content}"}
        ]
        return dicts

class LLMClientBase(metaclass=abc.ABCMeta):
    openai_client: OpenAI | None
    
    @abc.abstractmethod
    def _get_response(self, prompt: MessagePassingInterface) -> str:
        """
        Generate the response based on the prompt.
        :param prompt:
        :return:
        """
        return NotImplemented