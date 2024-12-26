import openai
from typing import Dict, Optional
from .base import LLMClient, MessageInterface


class OpenAIClient(LLMClient):

    def __init__(self, api_key: str):
        """
        Initialize the OpenAI client.

        :param api_key: The API key for OpenAI.
        :type api_key: str
        """
        super().__init__(api_key)
        openai.api_key = self.api_key

    def generate_text(self, prompt: MessageInterface, model: str = "gpt-3.5-turbo", **kwargs) -> Optional[Dict]:
        """
        Generate text using the OpenAI API.

        :param prompt: The prompt message.
        :type prompt: MessageInterface
        :param model: The model name to use, default is "gpt-3.5-turbo".
        :type model: str
        :param kwargs: Additional options such as max_tokens, temperature.
        :return: The response from OpenAI.
        :rtype: str
        """
        ai_completion = openai.ChatCompletion.create(
            model=model,
            messages=prompt.generate_prompt,
            **kwargs
        )
        return ai_completion.choices[0].message.content



    def validate_key(self):
        if not self.api_key:
            raise ValueError("API key is not provided.")

    def extract_keywords(self, content: str, prompt_template: str) -> str:
        """
        Extract keywords using the OpenAI API.

        :param content: The content to extract keywords from.
        :type content: str
        :param prompt_template: The prompt template for keyword extraction.
        :type prompt_template: str
        :return: The extracted keywords.
        :rtype: str
        """
        prompt = prompt_template.format(content=content)
        response = self.generate_text(prompt)
        if not response:
            raise RuntimeError("Failed to extract keywords: OpenAI API returned None")
        return response["choices"][0]["message"]["content"]

    def generate_summary(self, content: str, prompt_template: str) -> str:
        """
        Generate a summary using the OpenAI API.

        :param content: The content to generate a summary for.
        :type content: str
        :param prompt_template: The prompt template for summary generation.
        :type prompt_template: str
        :return: The generated summary.
        :rtype: str
        """
        prompt = prompt_template.format(content=content)
        response = self.generate_text(prompt)
        if not response:
            raise RuntimeError("Failed to generate summary: OpenAI API returned None")
        return response["choices"][0]["message"]["content"]
