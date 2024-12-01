import unittest
import os
from unittest.mock import patch, AsyncMock
from src.llm_client.openai_client import OpenAIClient

# 控制是否執行真實 API 測試
RUN_REAL_API_TESTS = "false"

class TestOpenAIClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """
        測試前的設置
        """
        if RUN_REAL_API_TESTS:
            self.client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = OpenAIClient(api_key="fake_api_key")

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    async def test_chat_completion_real(self):
        """
        測試真實的 chat completion API 呼叫
        """
        messages = [{"role": "user", "content": "你好，請問今天天氣如何？"}]
        response = await self.client.chat_completion(messages=messages, model="gpt-3.5-turbo")
        
        self.assertIn("content", response)
        self.assertIn("role", response)
        self.assertIn("usage", response)

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    async def test_embeddings_real(self):
        """
        測試真實的 embeddings API 呼叫
        """
        texts = ["這是一個測試文本"]
        embeddings = await self.client.embeddings(texts=texts, model="text-embedding-ada-002")
        
        self.assertTrue(isinstance(embeddings, list))
        self.assertTrue(isinstance(embeddings[0], list))
        self.assertTrue(all(isinstance(x, float) for x in embeddings[0]))

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    async def test_moderation_real(self):
        """
        測試真實的 moderation API 呼叫
        """
        texts = ["這是一個普通的句子"]
        result = await self.client.moderation(texts=texts)
        
        self.assertIn("results", result)
        self.assertTrue(isinstance(result["results"], list))
        self.assertIn("flagged", result["results"][0])

    @patch('openai.AsyncOpenAI')
    async def test_chat_completion_mock(self, mock_openai):
        """
        測試模擬的 chat completion
        """
        # 設置模擬回應
        mock_response = AsyncMock()
        mock_response.choices = [
            AsyncMock(
                message=AsyncMock(
                    content="模擬回應",
                    role="assistant"
                ),
                finish_reason="stop"
            )
        ]
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage = AsyncMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "測試訊息"}]
        response = await self.client.chat_completion(messages=messages, model="gpt-3.5-turbo")
        
        self.assertEqual(response["content"], "模擬回應")
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["usage"]["total_tokens"], 30)

    @patch('openai.AsyncOpenAI')
    async def test_embeddings_mock(self, mock_openai):
        """
        測試模擬的 embeddings
        """
        mock_response = AsyncMock()
        mock_response.data = [AsyncMock(embedding=[0.1, 0.2, 0.3])]
        
        mock_openai.return_value.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = ["測試文本"]
        embeddings = await self.client.embeddings(texts=texts, model="text-embedding-ada-002")
        
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])

    @patch('openai.AsyncOpenAI')
    async def test_moderation_mock(self, mock_openai):
        """
        測試模擬的 moderation
        """
        mock_response = AsyncMock()
        mock_response.results = [
            AsyncMock(
                flagged=False,
                categories={"violence": False, "hate": False},
                category_scores={"violence": 0.1, "hate": 0.1}
            )
        ]
        
        mock_openai.return_value.moderations.create = AsyncMock(return_value=mock_response)
        
        texts = ["測試文本"]
        result = await self.client.moderation(texts=texts)
        
        self.assertFalse(result["results"][0]["flagged"])
        self.assertIn("categories", result["results"][0])
        self.assertIn("category_scores", result["results"][0])

if __name__ == '__main__':
    unittest.main()
