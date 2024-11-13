from pydantic import BaseModel

class UserAuthSchema(BaseModel):
    username: str
    password: str

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchema(BaseModel):
    content: str

class Token(BaseModel):
    access_token: str
    token_type: str 