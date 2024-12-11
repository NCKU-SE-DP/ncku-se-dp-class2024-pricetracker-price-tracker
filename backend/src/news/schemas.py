from pydantic import BaseModel
from typing import Literal

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchema(BaseModel):
    content: str

class NewsSummaryCustomModelRequestSchema(BaseModel):
    content: str
    ai_model: str