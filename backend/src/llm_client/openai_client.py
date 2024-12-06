import json
import openai as OpenAI
from typing import Optional
from .base import LLMClientBase, MessagePassingInterface
from .prompts import Prompt_text

class OpenAIClient(LLMClientBase):
    def __init__(self, _api_key: str):
        try:
            OpenAI.api_key = _api_key
            self.openai_client = OpenAI
        except Exception as error:
            raise ValueError(f"Failed to initialize OpenAI client: {error}")
    
    def _generate_text(self, prompt: MessagePassingInterface) -> str:
        try:
            ai_completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
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
    
    def generate_summary(self, prompt_text: str) -> Optional[dict[str, str]]:
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