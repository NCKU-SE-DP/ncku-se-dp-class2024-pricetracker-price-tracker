import unittest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from src.llm_client.openai_client import OpenAIClient

# 控制是否執行真實 API 測試
RUN_REAL_API_TESTS = os.getenv("RUN_REAL_API_TESTS", "false").lower() == "true"

class TestOpenAIClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """
        測試前的設置
        """
        api_key = os.getenv("OPENAI_API_KEY", "fake_api_key")
        self.client = OpenAIClient(api_key=api_key)

    @patch('openai.AsyncOpenAI')
    async def test_chat_completion_mock(self, mock_openai_class):
        """
        測試模擬的 chat completion
        """
        # 設置模擬回應
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="模擬回應",
                    role="assistant"
                ),
                finish_reason="stop"
            )
        ]
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        # 設置模擬客戶端
        mock_completions = MagicMock()
        mock_completions.create = AsyncMock(return_value=mock_response)
        
        mock_chat = MagicMock()
        mock_chat.completions = mock_completions
        
        mock_client = MagicMock()
        mock_client.chat = mock_chat
        
        mock_openai_class.return_value = mock_client
        
        # 重新初始化客戶端以使用 mock
        self.client = OpenAIClient(api_key="fake_key")
        
        messages = [{"role": "user", "content": "測試訊息"}]
        response = await self.client.chat_completion(messages=messages)
        
        self.assertEqual(response["content"], "模擬回應")
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["usage"]["total_tokens"], 30)

    @patch('openai.AsyncOpenAI')
    async def test_embeddings_mock(self, mock_openai_class):
        """
        測試模擬的 embeddings
        """
        # 設置模擬回應
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1, 0.2, 0.3]
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding_data]
        
        # 設置模擬客戶端
        mock_embeddings = MagicMock()
        mock_embeddings.create = AsyncMock(return_value=mock_response)
        
        mock_client = MagicMock()
        mock_client.embeddings = mock_embeddings
        
        mock_openai_class.return_value = mock_client
        
        # 重新初始化客戶端以使用 mock
        self.client = OpenAIClient(api_key="fake_key")
        
        texts = ["測試文本"]
        embeddings = await self.client.embeddings(texts=texts)
        
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])

    @patch('openai.AsyncOpenAI')
    async def test_moderation_mock(self, mock_openai_class):
        """
        測試模擬的 moderation
        """
        # 設置模擬回應
        mock_result = MagicMock()
        mock_result.flagged = False
        mock_result.categories = {"violence": False, "hate": False}
        mock_result.category_scores = {"violence": 0.1, "hate": 0.1}
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        # 設置模擬客戶端
        mock_moderations = MagicMock()
        mock_moderations.create = AsyncMock(return_value=mock_response)
        
        mock_client = MagicMock()
        mock_client.moderations = mock_moderations
        
        mock_openai_class.return_value = mock_client
        
        # 重新初始化客戶端以使用 mock
        self.client = OpenAIClient(api_key="fake_key")
        
        texts = ["測試文本"]
        result = await self.client.moderation(texts=texts)
        
        self.assertFalse(result["results"][0]["flagged"])
        self.assertIn("categories", result["results"][0])
        self.assertIn("category_scores", result["results"][0])

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    async def test_chat_completion_real(self):
        """
        測試真實的 chat completion API 呼叫
        """
        messages = [{"role": "user", "content": "你好，請問今天天氣如何？"}]
        response = await self.client.chat_completion(messages=messages)
        
        self.assertIn("content", response)
        self.assertIn("role", response)
        self.assertIn("usage", response)

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    async def test_embeddings_real(self):
        """
        測試真實的 embeddings API 呼叫
        """
        texts = ["這是一個測試文本"]
        embeddings = await self.client.embeddings(texts=texts)
        
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

if __name__ == '__main__':
    unittest.main()
