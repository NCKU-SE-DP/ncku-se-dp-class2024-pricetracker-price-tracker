from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseLLMClient(ABC):
    """
    LLM 客戶端的基礎抽象類別。
    所有的 LLM 實現都應該繼承這個類別。
    """
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        執行聊天完成請求。

        Args:
            messages: 對話歷史訊息列表
            model: 要使用的模型名稱
            temperature: 溫度參數，控制輸出的隨機性 (0-1)
            max_tokens: 回應最大 token 數量
            **kwargs: 其他可選參數

        Returns:
            包含回應內容的字典
        """
        pass

    @abstractmethod
    async def embeddings(
        self,
        texts: List[str],
        model: str,
        **kwargs: Any
    ) -> List[List[float]]:
        """
        生成文本嵌入向量。

        Args:
            texts: 要進行嵌入的文本列表
            model: 要使用的嵌入模型名稱
            **kwargs: 其他可選參數

        Returns:
            嵌入向量列表
        """
        pass

    @abstractmethod
    async def moderation(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        執行內容審核。

        Args:
            texts: 要審核的文本列表
            model: 要使用的審核模型名稱
            **kwargs: 其他可選參數

        Returns:
            審核結果字典
        """
        pass
