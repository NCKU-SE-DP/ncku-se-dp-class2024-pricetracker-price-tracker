from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from .base import LLMClientProtocol

def create_openai_client(api_key: str) -> LLMClientProtocol:
    """
    建立 OpenAI 客戶端。

    Args:
        api_key: OpenAI API 金鑰

    Returns:
        符合 LLMClientProtocol 的客戶端
    """
    client = AsyncOpenAI(api_key=api_key)

    async def chat_completion(
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        使用 OpenAI 的 Chat API 執行對話完成。
        """
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            raise Exception(f"OpenAI Chat 完成請求失敗: {str(e)}")

    async def embeddings(
        texts: List[str],
        model: str = "text-embedding-ada-002",
        **kwargs: Any
    ) -> List[List[float]]:
        """
        使用 OpenAI 的 Embedding API 生成文本嵌入。
        """
        try:
            response = await client.embeddings.create(
                model=model,
                input=texts,
                **kwargs
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise Exception(f"OpenAI Embedding 請求失敗: {str(e)}")

    async def moderation(
        texts: List[str],
        model: Optional[str] = "text-moderation-latest",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        使用 OpenAI 的 Moderation API 執行內容審核。
        """
        try:
            response = await client.moderations.create(
                input=texts,
                model=model,
                **kwargs
            )
            return {
                "results": [{
                    "flagged": result.flagged,
                    "categories": result.categories,
                    "category_scores": result.category_scores
                } for result in response.results]
            }
        except Exception as e:
            raise Exception(f"OpenAI Moderation 請求失敗: {str(e)}")

    return type("OpenAIClient", (), {
        "chat_completion": chat_completion,
        "embeddings": embeddings,
        "moderation": moderation
    })()
