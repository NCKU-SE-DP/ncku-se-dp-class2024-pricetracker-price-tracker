from abc import abstractmethod, ABC
import json
import aisuite
from typing import Optional
from .prompts import Prompt_text
from .base import MessagePassingInterface, LLMClientBase

class LLMClientTemplate(LLMClientBase, ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model: str = ...
        self._initialize_client()

    # initialize client function should be abstract
    @abstractmethod
    def _initialize_client(self):
        ...

    def _generate_text(self, prompt: MessagePassingInterface) -> str:
        try:
            ai_completion = self.client.chat.completions.create(
                model=self.model,
                messages=prompt.to_dict
            )
            return ai_completion.choices[0].message.content
        except Exception as error:
            print(f"Failed to get response: {error}")
            return ""
    
    def extract_search(self, prompt_text: str) -> str:
        return self._generate_text(MessagePassingInterface(
            system_content=Prompt_text.keyword_extraction(),
            user_content=prompt_text
        ))
    
    def generate_summary(self, prompt_text: str) -> dict[str, str]:
        response = self._generate_text(MessagePassingInterface(
            system_content=Prompt_text.news_summary(),
            user_content=prompt_text
        ))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Failed to decode response")
    
    def evaluate_relevance(self, prompt_text: str) -> Optional[str]:
        response = self._generate_text(MessagePassingInterface(
            system_content=Prompt_text.relevance_assessment(),
            user_content=prompt_text
        ))
        if response not in ["high", "medium", "low"]:
            raise ValueError("Invalid response")
        return response