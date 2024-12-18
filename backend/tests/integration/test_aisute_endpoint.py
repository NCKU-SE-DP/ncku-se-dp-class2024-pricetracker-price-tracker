import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.config import settings
import aisuite as ai

client = TestClient(app)

@pytest.fixture
def ai_client():
    return ai.Client(api_key=settings.AISUITE_API_KEY)

async def test_chat_completion(ai_client):
    """測試聊天完成功能"""
    messages = [
        {"role": "user", "content": "你好，請用一句話描述今天的天氣"}
    ]
    
    response = await ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_chat_completion_with_system_message(ai_client):
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
    
    response = await ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_chat_completion_with_claude(ai_client):
    """測試 Claude 模型的聊天完成"""
    messages = [
        {"role": "user", "content": "你好，請用一句話描述今天的天氣"}
    ]
    
    response = await ai_client.chat.completions.create(
        model="claude-3-sonnet-20240229",
        messages=messages
    )
    
    assert response.choices[0].message.content is not None
    assert isinstance(response.choices[0].message.content, str)
    assert len(response.choices[0].message.content) > 0

async def test_chat_completion_error_handling(ai_client):
    """測試錯誤處理"""
    messages = [{"role": "invalid_role", "content": "test"}]
    
    with pytest.raises(Exception):
        await ai_client.chat.completions.create(
            model="invalid_model",
            messages=messages
        )

async def test_chat_completion_with_streaming(ai_client):
    """測試串流回應"""
    messages = [
        {"role": "user", "content": "請用一句話描述今天的天氣"}
    ]
    
    stream = await ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True
    )
    
    collected_content = ""
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            collected_content += chunk.choices[0].delta.content
    
    assert len(collected_content) > 0
    assert isinstance(collected_content, str)

async def test_chat_completion_with_function_call(ai_client):
    """測試函數調用功能"""
    messages = [
        {"role": "user", "content": "今天台北的天氣如何？"}
    ]
    
    functions = [
        {
            "name": "get_weather",
            "description": "獲取指定城市的天氣資訊",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名稱"
                    }
                },
                "required": ["city"]
            }
        }
    ]
    
    response = await ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    
    assert response.choices[0].message is not None
    if response.choices[0].message.function_call:
        assert response.choices[0].message.function_call.name == "get_weather"
        function_args = response.choices[0].message.function_call.arguments
        assert "city" in function_args
        assert "台北" in function_args

def test_embeddings():
    """測試文本嵌入 API"""
    request_body = {
        "texts": ["這是一個測試文本"]
    }
    
    response = client.post("/api/v1/news/news_summary_custom_model", json=request_body)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert isinstance(data[0], list)
    assert all(isinstance(x, float) for x in data[0])

def test_moderation():
    """測試內容審核 API"""
    request_body = {
        "texts": ["這是個普通的句子"]
    }
    
    response = client.post("/api/v1/openai/moderation", json=request_body)
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "flagged" in data["results"][0]
