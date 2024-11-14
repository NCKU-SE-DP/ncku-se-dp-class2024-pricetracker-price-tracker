from pydantic import BaseModel

class UserAuthSchema(BaseModel):
    """
    用於用戶註冊和登入的數據模式
    """
    username: str
    password: str



class PromptRequest(BaseModel):
    """
    用於新聞搜尋的關鍵字請求模式
    """
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    """
    用於新聞摘要生成的數據模式
    """
    content: str


class NewsArticleSchema(BaseModel):
    """
    用於回應的新聞文章數據模式
    """
    id: int
    url: str
    title: str
    time: str
    content: str
    summary: str
    reason: str

    class Config:
        orm_mode = True


class NewsUpvoteResponseSchema(BaseModel):
    """
    用於回應的新聞文章點贊數據模式
    """
    message: str
