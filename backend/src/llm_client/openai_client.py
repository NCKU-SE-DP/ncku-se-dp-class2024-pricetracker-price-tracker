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
            # self.openai_client = OpenAI(api_key=_api_key)
        except Exception as error:
            raise ValueError(f"Failed to initialize OpenAI client: {error}")
    
    def _get_response(self, prompt: MessagePassingInterface) -> str:
        try:
            ai_completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt.to_dict
            )
            return ai_completion.choices[0].message.content
        except Exception as error:
            print(f"Failed to get response: {error}")
            return ""
    
    def extract_keywords(self, prompt_text: str) -> str:
        return self._get_response(MessagePassingInterface(
            system_content=Prompt_text.keyword_extraction(),
            user_content=prompt_text
        ))
    
    def get_summary(self, prompt_text: str) -> Optional[dict[str, str]]:
        response = self._get_response(MessagePassingInterface(
            system_content=Prompt_text.news_summary(),
            user_content=prompt_text
        ))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Failed to decode response")
    
    def get_relevance_assessment(self, prompt_text: str) -> Optional[str]:
        response = self._get_response(MessagePassingInterface(
            system_content=Prompt_text.relevance_assessment(),
            user_content=prompt_text
        ))
        if response not in ["high", "medium", "low"]:
            raise ValueError("Invalid response")
        return response