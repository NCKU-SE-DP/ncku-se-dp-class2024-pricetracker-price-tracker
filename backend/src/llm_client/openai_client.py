import json
from openai import OpenAI, APIError, RateLimitError
from typing import Optional

from .base import LLMClientBase, MessageInterface
from .exceptions import LLMClientInitializeException, EvaluationFailure
from .config import get_ai_config
ai_config=get_ai_config()
class LLMClient(LLMClientBase):
    def __init__(self, _api_key: str = ai_config.OPEN_AI_KEY):
        try:
            self.openai_client = OpenAI(api_key=_api_key)
        except APIError as error:
            raise LLMClientInitializeException(f"Failed to initialize the LLM client due to an error: {error}")

    def _generate(self, prompt: MessageInterface) -> str:
        if ai_config.OPENAI_ENABLED:
            try:
                completion = self.openai_client.chat.completions.create(
                    model=ai_config.OPEN_AI_MODEL,
                    messages=prompt.to_dict,
                )
                return completion.choices[0].message.content
            except APIError as error:
                print(f"[OpenAI] An error occurred: {error}")
                return ""
            except RateLimitError as error:
                print(f"[OpenAI] Rate limit exceeded: {error}")
                return ""
        else:
            return ""

    def extract_search_keywords(self, prompt: str) -> str:
        """
        Extract search keywords from the prompt.
        :param prompt:
        :return:
        """
        return self._generate(MessageInterface(
            system_content="你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            user_content=prompt
        ))

    def generate_summary(self, prompt: str) -> Optional[dict[str, str]]:
        """
        Generate a summary based on the prompt.
        :param prompt:
        :return:
        """
        response = self._generate(MessageInterface(
            system_content="你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
            user_content=prompt,
        ))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise EvaluationFailure(f"Failed to generate a summary based on the prompt: {response}")

    def evaluate_relevance(self, news_title: str, prompt: str = "民生用品的價格變化") -> str:
        """
        Evaluate the relevance of the news title with the prompt.
        :param news_title:
        :param prompt:
        :return:
        """
        response = self._generate(MessageInterface(
            system_content=f"你是一個關聯度評估機器人，請評估新聞標題是否與「{prompt}」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            user_content=news_title
        ))
        return response