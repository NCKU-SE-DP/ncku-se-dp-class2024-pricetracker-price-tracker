import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.config import settings
import aisuite as ai

client = TestClient(app)

@pytest.fixture
def openai_client():
    return ai.Client(api_key=settings.OPENAI_API_KEY)

@pytest.fixture
def anthropic_client():
    return ai.Client(api_key=settings.ANTHROPIC_API_KEY)

async def test_openai_chat_completion(openai_client):
    """測試 OpenAI 聊天完成功能"""
    messages = [
        {"role": "user", "content": "你好，請用一句話描述今天的天氣"}
    ]
    
    response = await openai_client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_anthropic_chat_completion(anthropic_client):
    """測試 Anthropic 聊天完成功能"""
    messages = [
        {"role": "user", "content": "你好，請用一句話描述今天的天氣"}
    ]
    
    response = await anthropic_client.chat.completions.create(
        model=settings.ANTHROPIC_MODEL,
        messages=messages
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_openai_chat_completion_with_system_message(openai_client):
    """測試帶有系統訊息的聊天完成"""
    messages = [
        {
            "role": "system",
            "content": "你是一個天氣預報機器人，請用簡短的一句話回答"
        },
        {
            "role": "user",
            "content": "今天天氣如何？"
        }
    ]
    
    response = await openai_client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.7
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_openai_chat_completion_error_handling(openai_client):
    """測試錯誤處理"""
    messages = [{"role": "invalid_role", "content": "test"}]
    
    with pytest.raises(Exception):
        await openai_client.chat.completions.create(
            model="invalid_model",
            messages=messages
        )

async def test_anthropic_chat_completion_error_handling(anthropic_client):
    """測試 Anthropic 錯誤處理"""
    messages = [{"role": "invalid_role", "content": "test"}]
    
    with pytest.raises(Exception):
        await anthropic_client.chat.completions.create(
            model="invalid_model",
            messages=messages
        )

async def test_openai_embeddings(openai_client):
    """測試 OpenAI 文本嵌入"""
    texts = ["這是一個測試文本"]
    
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    
    assert response.data is not None
    assert len(response.data) > 0
    assert len(response.data[0].embedding) > 0
    assert all(isinstance(x, float) for x in response.data[0].embedding)

@pytest.mark.skipif(
    not settings.ANTHROPIC_API_KEY, 
    reason="需要 Anthropic API key"
)
async def test_anthropic_streaming(anthropic_client):
    """測試 Anthropic 串流回應"""
    messages = [
        {"role": "user", "content": "請用一句話描述今天的天氣"}
    ]
    
    stream = await anthropic_client.chat.completions.create(
        model=settings.ANTHROPIC_MODEL,
        messages=messages,
        stream=True
    )
    
    collected_content = ""
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            collected_content += chunk.choices[0].delta.content
    
    assert len(collected_content) > 0
    assert isinstance(collected_content, str)
