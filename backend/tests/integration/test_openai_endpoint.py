import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_chat_completion():
    """測試聊天完成 API"""
    request_body = {
        "messages": [
            {"role": "user", "content": "你好，請問今天天氣如何？"}
        ]
    }
    
    response = client.post("/api/v1/openai/chat", json=request_body)
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert isinstance(data["content"], str)

def test_embeddings():
    """測試文本嵌入 API"""
    request_body = {
        "texts": ["這是一個測試文本"]
    }
    
    response = client.post("/api/v1/openai/embeddings", json=request_body)
    
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
