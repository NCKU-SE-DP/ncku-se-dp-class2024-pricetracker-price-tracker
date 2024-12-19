from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from .base import LLMClient, MessageInterface
import json


class LLMClientTemplate(LLMClient, ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self):        
        pass

    def generate_text(self, prompt: MessageInterface) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=prompt.generate_prompt,
        )
        return completion.choices[0].message.content
    
    def extract_keyword(self, prompt: str) -> str:
        
        return self.generate_text(MessageInterface(
            system_content="你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            user_content=prompt
        ))
    

    def generate_summary(self, prompt: str) -> str:
        
        response = self.generate_text(MessageInterface(
            system_content='你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {"影響": "...", "原因": "..."})，並請確保返回有效 json 格式',
            user_content=prompt
        ))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to generate a summary based on the prompt: {response}")

    def get_relevance_assessment(self, prompt: str) -> str:
        
        return self.generate_text(MessageInterface(
            system_content="你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            user_content=prompt
        ))
        
