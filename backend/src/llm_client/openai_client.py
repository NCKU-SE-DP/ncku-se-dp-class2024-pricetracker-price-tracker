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

    class OpenAIClientImpl:
        async def chat_completion(
            self,
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
                raise Exception(f"OpenAI 請求失敗: {str(e)}")

    return OpenAIClientImpl()
